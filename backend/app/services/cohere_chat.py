import json
import re
from typing import Any, Dict, List

import cohere

from app.config import get_settings


SYSTEM_PROMPTS = {
    "ar": """أنت موظف استقبال ذكي لشكاوى شركة العاصمة الإدارية. مهمتك جمع تفاصيل الشكوى تدريجيًا، سؤال واحد في كل مرة، دون تكرار سؤال تمت الإجابة عنه.

اقرأ سجل المحادثة كاملًا واستخرج المعلومات التي ذكرها المستخدم عبر كل الرسائل. لا تطلب من المستخدم إعادة معلومات قدمها بالفعل. اسأل فقط عن أهم معلومة ناقصة، بصياغة محددة وطبيعية، ولا تسأل عن عدة أشياء في رسالة واحدة.

اجمع هذه الحقول المطلوبة قبل اعتبار المسودة جاهزة:
- وصف واضح للمشكلة وتأثيرها (description).
- الحي أو المنطقة (district).
- الشارع أو أقرب معلم (address).
- وقت بداية المشكلة: today أو week أو month أو unknown. إذا قال المستخدم إنه لا يعرف، استخدم unknown ولا تواصل سؤاله عن هذا الحقل.
- صنّف نوع الشكوى إلى واحدة من: lighting, roads, waste, water, parking, noise, other. استخدم other عندما لا تناسب المشكلة الفئات الأخرى، مثل وجود كلاب كثيرة.

لا تطلب الاسم أو الهاتف أو الموافقة داخل المحادثة؛ سيُدخل المستخدم بيانات التواصل ويوافق من نموذج الشكوى. لا تختلق تفاصيل أو تعتبر موقعًا غير واضح مؤكدًا. إذا كانت معلومة موجودة في كلام المستخدم، استخرجها ولا تسأل عنها مجددًا.

عندما تكتمل الحقول الأربعة (description وdistrict وaddress وonset) وتكون الفئة محددة، أعد ready_for_review=true، واكتب ملخصًا موجزًا في summary، واطلب من المستخدم مراجعة التفاصيل والضغط على زر استخدام التفاصيل في النموذج لإكمال بياناته وتقديم الشكوى. لا تدّعِ أن الشكوى أُرسلت أو سُجلت.

أعد JSON صالحًا فقط، دون Markdown أو نص خارجه، وبالمفاتيح التالية بالضبط:
{"reply":"رد للمستخدم باللغة العربية","ready_for_review":false,"summary":"","category":null,"district":null,"address":null,"description":null,"onset":null}
استخدم القيم المستخرجة للحقول، وضع null فقط إذا لم تُعرف بعد. عند عدم اكتمال الحقول، ready_for_review=false واسأل عن حقل واحد ناقص فقط.""",
    "en": """You are an intelligent intake assistant for New Administrative Capital complaints. Collect details gradually, asking one question at a time without repeating questions already answered.

Read the full conversation history and extract facts across all messages. Never ask the user to repeat information they have already provided. Ask only for the most important missing field, clearly and naturally; do not ask multiple questions in one turn.

Collect these fields before marking the draft ready:
- Clear issue description and impact (description).
- District/area (district).
- Street or nearest landmark (address).
- Onset: today, week, month, or unknown. If the user does not know, use unknown and do not ask again.
- Classify as one of: lighting, roads, waste, water, parking, noise, other. Use other when no listed category fits, such as many stray dogs.

Do not ask for name, phone, or consent in chat; the user will enter those in the complaint form. Do not invent facts or treat an unclear location as confirmed. If a fact is already present in the user's messages, extract it instead of asking again.

When description, district, address, and onset are known (onset may be unknown) and a category is selected, set ready_for_review=true, provide a concise summary, and ask the user to review the details and click the Use details in form button to complete contact details and submit. Never claim that a complaint has already been submitted or registered.

Return valid JSON only, with no Markdown or text outside JSON, using exactly these keys:
{"reply":"user-facing reply in English","ready_for_review":false,"summary":"","category":null,"district":null,"address":null,"description":null,"onset":null}
Use extracted values for fields and null only when not known yet. If required details are missing, ready_for_review=false and ask about only one missing field.""",
}


def _get_history_item(item: Any) -> tuple[str, str]:
    if isinstance(item, dict):
        role, content = item.get("role"), item.get("content")
    else:
        role, content = getattr(item, "role", None), getattr(item, "content", None)
    if role not in ("user", "assistant") or not isinstance(content, str):
        return "", ""
    return role, content.strip()


def _response_text(response: Any) -> str:
    content = getattr(getattr(response, "message", None), "content", None) or []
    parts = []
    for item in content:
        text = getattr(item, "text", None)
        if text:
            parts.append(text)
        elif isinstance(item, dict) and item.get("text"):
            parts.append(item["text"])
    return "\n".join(parts).strip()


def _parse_json(raw: str) -> Dict[str, Any]:
    candidate = raw.strip()
    if candidate.startswith("```"):
        candidate = re.sub(r"^```(?:json)?\s*|\s*```$", "", candidate, flags=re.IGNORECASE)
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", candidate, flags=re.DOTALL)
        if not match:
            raise ValueError("Cohere returned a response that was not valid JSON")
        parsed = json.loads(match.group(0))
    if not isinstance(parsed, dict) or not isinstance(parsed.get("reply"), str):
        raise ValueError("Cohere response is missing the reply field")
    return parsed


def generate_reply(language: str, message: str, history: List[Any]) -> Dict[str, Any]:
    settings = get_settings()
    if not settings.cohere_api_key:
        raise ValueError("COHERE_API_KEY is not configured")

    client = cohere.ClientV2(api_key=settings.cohere_api_key)
    prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["ar"])
    messages = [{"role": "system", "content": prompt}]

    for item in history[-20:]:
        role, content = _get_history_item(item)
        if role and content:
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": message})
    response = client.chat(model=settings.cohere_model, messages=messages)
    raw = _response_text(response)
    result = _parse_json(raw)

    allowed_categories = {"lighting", "roads", "waste", "water", "parking", "noise", "other"}
    allowed_onsets = {"today", "week", "month", "unknown"}
    category = result.get("category")
    onset = result.get("onset")
    if category not in allowed_categories:
        category = None
    if onset not in allowed_onsets:
        onset = None

    ready = bool(result.get("ready_for_review"))
    district = result.get("district") if isinstance(result.get("district"), str) else None
    address = result.get("address") if isinstance(result.get("address"), str) else None
    description = result.get("description") if isinstance(result.get("description"), str) else None
    summary = result.get("summary") if isinstance(result.get("summary"), str) else None

    # Enforce basic readiness server-side so the model cannot prematurely unlock review.
    ready = ready and bool(district and district.strip()) and bool(address and address.strip()) \
        and bool(description and len(description.strip()) >= 8) and bool(onset and category)

    return {
        "reply": result["reply"],
        "ready_for_review": ready,
        "summary": summary,
        "category": category,
        "district": district,
        "address": address,
        "description": description,
        "onset": onset,
    }
