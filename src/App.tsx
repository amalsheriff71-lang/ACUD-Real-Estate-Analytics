import { useMemo, useState, type FormEvent, type ReactNode } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Check,
  ChevronDown,
  ClipboardList,
  Clock3,
  FileText,
  Globe2,
  Headphones,
  MapPin,
  MessageCircle,
  ShieldCheck,
  UploadCloud,
  X,
  Building2,
  Lightbulb,
  Route,
  Trash2,
  Droplets,
  CarFront,
  Volume2,
  MoreHorizontal,
  Send,
  Sparkles,
} from "lucide-react";

import LandingPage from "./components/LandingPage";


type DistrictId =
  | "district_1"
  | "district_2"
  | "district_3"
  | "district_4"
  | "district_5"
  | "government_district";

const districts: {
  id: DistrictId;
  ar: string;
  en: string;
}[] = [
  { id: "district_1", ar: "الحي السكني الأول", en: "First Residential District" },
  { id: "district_2", ar: "الحي السكني الثاني", en: "Second Residential District" },
  { id: "district_3", ar: "الحي السكني الثالث", en: "Third Residential District" },
  { id: "district_4", ar: "الحي السكني الرابع", en: "Fourth Residential District" },
  { id: "district_5", ar: "الحي السكني الخامس", en: "Fifth Residential District" },
  { id: "government_district", ar: "الحي الحكومي", en: "Government District" },
];


type Language = "ar" | "en";

type Category =
  | "lighting"
  | "roads"
  | "waste"
  | "water"
  | "parking"
  | "noise"
  | "other";

const categories: {
  id: Category;
  en: string;
  ar: string;
  icon: typeof Lightbulb;
}[] = [
  { id: "lighting", en: "Street lighting", ar: "إنارة الشوارع", icon: Lightbulb },
  { id: "roads", en: "Roads and pavements", ar: "الطرق والأرصفة", icon: Route },
  { id: "waste", en: "Waste build-up", ar: "تراكم المخلفات", icon: Trash2 },
  { id: "water", en: "Water leak", ar: "تسرب مياه", icon: Droplets },
  { id: "parking", en: "Parking violations", ar: "مخالفات الانتظار", icon: CarFront },
  { id: "noise", en: "Noise", ar: "ضوضاء", icon: Volume2 },
  { id: "other", en: "Other complaint", ar: "شكوى أخرى", icon: MoreHorizontal },
];

const copy = {
  ar: {
    brand: "العاصمة الإدارية الجديدة",
    portal: "منصة الشكاوى والمقترحات",
    home: "الرئيسية",
    track: "متابعة شكوى",
    help: "مركز المساعدة",
    eyebrow: "معًا لمدينة أفضل",
    title: "صوتك يصنع الفرق.",
    subtitle:
      "أبلغنا عن مشكلة في منطقتك، وسنعمل على توصيلها إلى الفريق المختص.",
    secure: "بياناتك محمية",
    fast: "تقديم سهل وسريع",
    official: "قناة التواصل الرسمية",
    formTitle: "تقديم شكوى جديدة",
    formSub: "يرجى إدخال التفاصيل التالية لمساعدتنا في التعامل مع بلاغك.",
    step: "الخطوة 1 من 2",
    personal: "بيانات مقدم الشكوى",
    fullName: "الاسم بالكامل",
    phone: "رقم الهاتف",
    email: "البريد الإلكتروني (اختياري)",
    category: "نوع الشكوى",
    choose: "اختر نوع الشكوى",
    location: "موقع المشكلة",
    area: "الحي / المنطقة",
    areaPlaceholder: "مثال: الحي السكني الثالث",
    address: "الشارع أو أقرب معلم",
    addressPlaceholder: "اسم الشارع، رقم المبنى أو علامة مميزة",
    details: "تفاصيل الشكوى",
    description: "وصف المشكلة",
    descriptionPlaceholder:
      "اشرح المشكلة ومكانها وأي تفاصيل قد تساعدنا...",
    date: "متى بدأت المشكلة؟",
    today: "اليوم",
    week: "خلال الأسبوع",
    month: "منذ أكثر من شهر",
    unknown: "غير متأكد",
    attachment: "صور أو مستندات (اختياري)",
    upload: "اضغط لرفع الملفات أو اسحبها هنا",
    fileTypes: "PNG, JPG أو PDF — بحد أقصى 10 ميجابايت",
    consent:
      "أقر بصحة البيانات المدخلة وأوافق على استخدامها لمعالجة الشكوى.",
    submit: "إرسال الشكوى",
    required: "الحقول التي تحمل علامة * مطلوبة",
    sideTitle: "كيف تعمل المنصة؟",
    sideSub: "خطوات بسيطة لمتابعة بلاغك",
    step1: "أرسل تفاصيل المشكلة",
    step1sub: "املأ النموذج وأرفق صورة إن أمكن.",
    step2: "تصل للفريق المختص",
    step2sub: "يتم توجيه البلاغ إلى الإدارة المعنية.",
    step3: "تابع حالة الشكوى",
    step3sub: "احتفظ برقم الشكوى لمتابعتها لاحقًا.",
    noteTitle: "هل لديك شكوى مختلفة؟",
    note:
      "يمكن للمساعد الذكي إرشادك للأسئلة والتفاصيل المطلوبة حسب نوع المشكلة.",
    chat: "ابدأ مع المساعد الذكي",
    footer: "جميع الحقوق محفوظة © العاصمة الإدارية الجديدة",
    privacy: "الخصوصية",
    terms: "الشروط والأحكام",
    chatbotTitle: "المساعد الذكي للشكاوى",
    chatbotIntro:
      "سأساعدك في توضيح نوع الشكوى وجمع التفاصيل اللازمة قبل إرسالها.",
    chatbotPrompt: "ما المشكلة التي تريد الإبلاغ عنها؟",
    chatPlaceholder: "اكتب وصفًا مختصرًا للمشكلة...",
    send: "إرسال",
    close: "إغلاق",
    chatHint:
      "مساعد ذكي يجمع التفاصيل، ثم يساعدك في مراجعتها قبل تقديم الشكوى.",
    otherRequired: "لنتعرف على تفاصيل الشكوى",
    otherHelp:
      "اكتب وصفًا مختصرًا، وسأطرح عليك أسئلة توضيحية لتجهيز البلاغ.",
    chatbotNext: "متابعة",
    chatbotDone: "تم جمع التفاصيل",
    chatDoneText:
      "أصبحت لديك مسودة تفاصيل يمكنك نسخها إلى نموذج الشكوى.",
    useDetails: "استخدام التفاصيل في النموذج",
    copied: "تم تجهيز ملخص الشكوى",
    successTitle: "تم تجهيز الشكوى",
    successText:
      "تم حفظ الشكوى بنجاح. احتفظ برقم المرجع لمتابعتها لاحقًا.",
    successClose: "العودة للنموذج",
    summary: "ملخص الشكوى",
    closeModal: "إغلاق",
    selectIssue: "يرجى اختيار نوع الشكوى.",
    fillRequired:
      "يرجى استكمال الحقول المطلوبة والموافقة على الإقرار.",
  },
  en: {
    brand: "New Administrative Capital",
    portal: "Complaints & Suggestions Portal",
    home: "Home",
    track: "Track a complaint",
    help: "Help center",
    eyebrow: "Together for a better city",
    title: "Your voice makes a difference.",
    subtitle:
      "Report an issue in your area and we’ll help direct it to the relevant team.",
    secure: "Your data is protected",
    fast: "Simple and quick",
    official: "Official communication channel",
    formTitle: "Submit a new complaint",
    formSub:
      "Enter the details below so we can better understand your report.",
    step: "Step 1 of 2",
    personal: "Complainant information",
    fullName: "Full name",
    phone: "Phone number",
    email: "Email address (optional)",
    category: "Complaint category",
    choose: "Select a complaint type",
    location: "Issue location",
    area: "District / Area",
    areaPlaceholder: "e.g. Third Residential District",
    address: "Street or nearest landmark",
    addressPlaceholder: "Street name, building number, or landmark",
    details: "Complaint details",
    description: "Describe the issue",
    descriptionPlaceholder:
      "Explain the issue, where it is, and any details that may help...",
    date: "When did the issue begin?",
    today: "Today",
    week: "Within the past week",
    month: "More than a month ago",
    unknown: "Not sure",
    attachment: "Photos or documents (optional)",
    upload: "Click to upload or drag files here",
    fileTypes: "PNG, JPG or PDF — up to 10 MB",
    consent:
      "I confirm the information provided is accurate and consent to its use to process this complaint.",
    submit: "Submit complaint",
    required: "Fields marked * are required",
    sideTitle: "How it works",
    sideSub: "A few simple steps to report an issue",
    step1: "Tell us what happened",
    step1sub: "Complete the form and attach a photo if possible.",
    step2: "Sent to the relevant team",
    step2sub: "Your report can be routed to the appropriate department.",
    step3: "Follow your complaint",
    step3sub: "Keep your reference number to check progress later.",
    noteTitle: "Something else to report?",
    note:
      "Our smart assistant can guide you through the questions and details needed for other issues.",
    chat: "Talk to the smart assistant",
    footer: "All rights reserved © New Administrative Capital",
    privacy: "Privacy",
    terms: "Terms & conditions",
    chatbotTitle: "Smart complaint assistant",
    chatbotIntro:
      "I can help clarify your complaint type and gather the details needed before you submit it.",
    chatbotPrompt: "What issue would you like to report?",
    chatPlaceholder: "Briefly describe the issue...",
    send: "Send",
    close: "Close",
    chatHint:
      "The AI assistant gathers details and helps you review them before submitting.",
    otherRequired: "Let's clarify your complaint",
    otherHelp:
      "Describe the issue briefly. I'll ask follow-up questions to help prepare your report.",
    chatbotNext: "Continue",
    chatbotDone: "Details collected",
    chatDoneText:
      "You now have a draft summary you can use in the complaint form.",
    useDetails: "Use details in form",
    copied: "Complaint summary prepared",
    successTitle: "Complaint prepared",
    successText:
      "Your complaint was saved successfully. Keep the reference number to track it later.",
    successClose: "Back to form",
    summary: "Complaint summary",
    closeModal: "Close",
    selectIssue: "Please select a complaint category.",
    fillRequired:
      "Please complete the required fields and confirm the declaration.",
  },
};

type ChatMessage = {
  from: "bot" | "user";
  text: string;
};

type ChatExtracted = {
  category?: Category | null;
  district?: string | null;
  address?: string | null;
  description?: string | null;
  onset?: "today" | "week" | "month" | "unknown" | null;
};

type ChatApiResponse = {
  reply: string;
  provider: string;
  model: string;
  ready_for_review: boolean;
  summary?: string | null;
  category?: Category | null;
  district?: string | null;
  address?: string | null;
  description?: string | null;
  onset?: "today" | "week" | "month" | "unknown" | null;
};

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export default function App() {
  // Portal navigation: landing, resident complaints, or investor services.
  const [portal, setPortal] = useState<
    "landing" | "resident" | "investor"
  >("landing");
  const [districtQuery, setDistrictQuery] = useState("");

  const [lang, setLang] = useState<Language>("ar");
  const [category, setCategory] = useState<Category | "">("");
  const [chatOpen, setChatOpen] = useState(false);
  const [chatInput, setChatInput] = useState("");
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([]);
  const [chatLoading, setChatLoading] = useState(false);
  const [chatReadyForReview, setChatReadyForReview] = useState(false);
  const [chatExtracted, setChatExtracted] =
    useState<ChatExtracted | null>(null);
  const [showSuccess, setShowSuccess] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [referenceNumber, setReferenceNumber] = useState("");
  const [formError, setFormError] = useState("");
  const [fileName, setFileName] = useState("");

  const [form, setForm] = useState({
    name: "",
    phone: "",
    email: "",
    area: "" as DistrictId | "",
    address: "",
    description: "",
    onset: "",
    consent: false,
  });

  const t = copy[lang];
  const rtl = lang === "ar";
  const Arrow = rtl ? ArrowLeft : ArrowRight;

  const selectedCategory = useMemo(
    () => categories.find((c) => c.id === category),
    [category]
  );

  const normalizeDistrict = (
    value?: string | null
  ): DistrictId | "" => {
    if (!value) return "";

    const trimmed = value.trim();
    return districts.some((district) => district.id === trimmed)
      ? (trimmed as DistrictId)
      : "";
  };

  const update = (
    key: keyof typeof form,
    value: string | boolean
  ) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const openChat = () => {
    setChatOpen(true);

    if (chatMessages.length === 0) {
      setChatReadyForReview(false);
      setChatExtracted(null);
      setChatMessages([
        { from: "bot", text: t.chatbotIntro },
        { from: "bot", text: t.chatbotPrompt },
      ]);
    }
  };

  const sendChat = async () => {
    const value = chatInput.trim();

    if (!value || chatLoading) return;

    const history = chatMessages.map((msg) => ({
      role:
        msg.from === "user"
          ? ("user" as const)
          : ("assistant" as const),
      content: msg.text,
    }));

    setChatMessages((prev) => [
      ...prev,
      { from: "user", text: value },
    ]);
    setChatInput("");
    setChatLoading(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language: lang,
          message: value,
          history,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          typeof data.detail === "string"
            ? data.detail
            : "Chat request failed"
        );
      }

      const result = data as ChatApiResponse;

      setChatMessages((prev) => [
        ...prev,
        { from: "bot", text: result.reply },
      ]);

      setChatReadyForReview(Boolean(result.ready_for_review));

      setChatExtracted({
        category: result.category,
        district: result.district,
        address: result.address,
        description: result.description,
        onset: result.onset,
      });
    } catch (error) {
      console.error("Chat request failed:", error);

      setChatMessages((prev) => [
        ...prev,
        {
          from: "bot",
          text:
            lang === "ar"
              ? "عذرًا، تعذر الاتصال بالمساعد الآن. تأكدي من تشغيل الخادم ثم حاولي مرة أخرى."
              : "Sorry, I couldn't reach the assistant. Check that the backend is running and try again.",
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const useChatDetails = () => {
    if (!chatReadyForReview) return;

    const transcript = chatMessages
      .filter((m) => m.from === "user")
      .map((m) => m.text)
      .join("\n");

    setForm((prev) => ({
      ...prev,
      area: normalizeDistrict(chatExtracted?.district) || prev.area,
      address: chatExtracted?.address?.trim() || prev.address,
      description:
        chatExtracted?.description?.trim() ||
        transcript ||
        prev.description,
      onset: chatExtracted?.onset || prev.onset,
    }));

    setCategory(chatExtracted?.category || "other");
    setChatOpen(false);

    document
      .getElementById("complaint-form")
      ?.scrollIntoView({ behavior: "smooth" });
  };

  
const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
  e.preventDefault();

  if (!category) {
    setFormError(t.selectIssue);
    return;
  }

  if (
    !form.name.trim() ||
    !form.phone.trim() ||
    !form.area ||
    !form.address.trim() ||
    !form.description.trim() ||
    !form.onset ||
    !form.consent
  ) {
    setFormError(t.fillRequired);
    return;
  }

  // Ensure the selected district is one of the allowed options.
  const selectedDistrict = districts.find(
    (district) => district.id === form.area
  );

  if (!selectedDistrict) {
    setFormError(
      lang === "ar"
        ? "يرجى اختيار حي صحيح من القائمة."
        : "Please select a valid district from the list."
    );
    return;
  }

  setFormError("");
  setSubmitLoading(true);

  try {
    const payload = {
      language: lang,
      full_name: form.name.trim(),
      phone: form.phone.trim(),
      email: form.email.trim() || null,
      category,
      district: selectedDistrict.id,
      address: form.address.trim(),
      description: form.description.trim(),
      onset: form.onset,
      consent: form.consent,
      attachment_name: fileName || null,
    };

    const response = await fetch(
      `${API_BASE_URL}/api/v1/complaints`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }
    );

    const data = await response.json();

    if (!response.ok) {
      const detail =
        typeof data.detail === "string"
          ? data.detail
          : "Complaint submission failed";

      throw new Error(detail);
    }

    setReferenceNumber(data.reference_number);
    setShowSuccess(true);
  } catch (error) {
    console.error("Complaint submission failed:", error);

    setFormError(
      lang === "ar"
        ? "تعذر إرسال الشكوى. تأكدي من تشغيل الخادم وصحة البيانات، ثم حاولي مرة أخرى."
        : "The complaint could not be submitted. Check the backend and your details, then try again."
    );
  } finally {
    setSubmitLoading(false);
  }
};


  // IMPORTANT:
  // All hooks are declared above the conditional returns.
  // This avoids the React Rules of Hooks error.

  if (portal === "landing") {
    return (
      <LandingPage
        onSelectResident={() => setPortal("resident")}
        onSelectInvestor={() => setPortal("investor")}
      />
    );
  }

  if (portal === "investor") {
    return (
      <main
        dir={rtl ? "rtl" : "ltr"}
        className="min-h-screen bg-[#EEEEEE] p-6 text-[#1D1616] md:p-12"
      >
        <div className="mx-auto max-w-5xl">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <button
              type="button"
              onClick={() => setPortal("landing")}
              className="rounded-xl border border-stone-300 bg-white px-4 py-2 font-semibold transition hover:bg-stone-100"
            >
              {rtl ? "العودة للرئيسية" : "Back to home"}
            </button>

            <button
              type="button"
              onClick={() => setLang(rtl ? "en" : "ar")}
              className="flex items-center gap-2 rounded-xl border border-stone-300 bg-white px-4 py-2 font-semibold transition hover:bg-stone-100"
            >
              <Globe2 size={17} />
              {rtl ? "English" : "العربية"}
            </button>
          </div>

          <section className="mx-auto mt-12 max-w-3xl rounded-3xl bg-white p-8 shadow-sm md:p-12">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[#8E1616]/10 text-[#8E1616]">
              <Building2 size={28} />
            </div>

            <h1 className="mt-6 text-3xl font-black md:text-4xl">
              {rtl ? "خدمات المستثمرين" : "Investor Services"}
            </h1>

            <p className="mt-4 leading-8 text-stone-600">
              {rtl
                ? "مرحبًا بك في بوابة المستثمرين بالعاصمة الإدارية الجديدة. سيتم إضافة خدمات الاستفسارات الاستثمارية وتقديم الطلبات ومتابعتها في هذه الصفحة."
                : "Welcome to the New Administrative Capital investor portal. Investment inquiries, service requests, and request tracking can be added to this page."}
            </p>

            <div className="mt-8 grid gap-4 sm:grid-cols-2">
              <div className="rounded-2xl border border-stone-200 p-5">
                <Building2 className="text-[#8E1616]" size={24} />
                <h2 className="mt-3 font-bold">
                  {rtl ? "الاستفسارات الاستثمارية" : "Investment inquiries"}
                </h2>
                <p className="mt-2 text-sm leading-6 text-stone-500">
                  {rtl
                    ? "تقديم الاستفسارات المتعلقة بالاستثمار والخدمات."
                    : "Submit inquiries about investment opportunities and services."}
                </p>
              </div>

              <div className="rounded-2xl border border-stone-200 p-5">
                <ClipboardList className="text-[#8E1616]" size={24} />
                <h2 className="mt-3 font-bold">
                  {rtl ? "متابعة الطلبات" : "Request tracking"}
                </h2>
                <p className="mt-2 text-sm leading-6 text-stone-500">
                  {rtl
                    ? "إمكانية متابعة الطلبات المقدمة مستقبلًا."
                    : "Track submitted requests when this feature becomes available."}
                </p>
              </div>
            </div>

            <p className="mt-8 rounded-xl bg-stone-50 p-4 text-sm leading-6 text-stone-500">
              {rtl
                ? "هذه صفحة مبدئية، ولم يتم ربط خدمات المستثمرين بنظام خلفي بعد."
                : "This is a placeholder page. Investor services are not connected to a backend yet."}
            </p>

            <button
              type="button"
              onClick={() => setPortal("landing")}
              className="mt-6 rounded-xl bg-[#8E1616] px-6 py-3 font-bold text-white transition hover:bg-[#D84040]"
            >
              {rtl ? "العودة للرئيسية" : "Return to home"}
            </button>
          </section>
        </div>
      </main>
    );
  }

  // Resident portal: your original complaints page.
  return (
    <div
      dir={rtl ? "rtl" : "ltr"}
      className="min-h-screen bg-[#F7F6F6] text-ink"
    >
      <header className="border-b border-black/5 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <button
            type="button"
            onClick={() => setPortal("landing")}
            className="flex items-center gap-3 text-start"
            aria-label={t.brand}
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-ink text-white shadow-sm">
              <Building2 size={25} />
            </div>

            <div>
              <div className="text-sm font-extrabold text-ink sm:text-base">
                {t.brand}
              </div>
              <div className="mt-0.5 text-xs text-stone-500">
                {t.portal}
              </div>
            </div>
          </button>

          <nav className="hidden items-center gap-7 text-sm font-semibold text-stone-600 md:flex">
            <button
              type="button"
              className="transition hover:text-signal"
              onClick={() => setPortal("landing")}
            >
              {t.home}
            </button>

            <a
              className="transition hover:text-signal"
              href="#complaint-form"
            >
              {t.track}
            </a>

            <button
              type="button"
              onClick={openChat}
              className="transition hover:text-signal"
            >
              {t.help}
            </button>
          </nav>

          <button
            type="button"
            onClick={() => setLang(rtl ? "en" : "ar")}
            className="flex items-center gap-2 rounded-xl border border-stone-200 px-3 py-2 text-sm font-bold transition hover:border-signal hover:text-maroon"
            aria-label="Switch language"
          >
            <Globe2 size={17} />
            <span>{rtl ? "English" : "العربية"}</span>
          </button>
        </div>
      </header>

      <main id="top">
        <section className="relative overflow-hidden bg-ink text-white">
          <div className="absolute inset-0 opacity-20" aria-hidden="true">
            <div className="absolute -end-16 -top-32 h-96 w-96 rounded-full border-[48px] border-signal" />
            <div className="absolute -bottom-48 start-[28%] h-96 w-96 rounded-full border border-white" />
            <div className="absolute bottom-8 end-[18%] h-24 w-24 rotate-12 rounded-3xl border border-white" />
          </div>

          <div className="relative mx-auto grid max-w-7xl gap-10 px-4 py-14 sm:px-6 md:grid-cols-[1.3fr_.7fr] md:items-center md:py-20 lg:px-8">
            <div>
              <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/5 px-4 py-2 text-sm text-red-100">
                <span className="h-2 w-2 rounded-full bg-signal" />
                {t.eyebrow}
              </div>

              <h1 className="max-w-2xl text-4xl font-black leading-tight tracking-tight sm:text-5xl lg:text-6xl">
                {t.title}
              </h1>

              <p className="mt-5 max-w-xl text-base leading-8 text-white/70 sm:text-lg">
                {t.subtitle}
              </p>

              <div className="mt-8 flex flex-wrap gap-3">
                {[
                  { icon: ShieldCheck, text: t.secure },
                  { icon: Clock3, text: t.fast },
                ].map(({ icon: Icon, text }) => (
                  <div
                    key={text}
                    className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-3 py-2.5 text-sm text-white/85"
                  >
                    <Icon size={17} className="text-red-300" />
                    {text}
                  </div>
                ))}
              </div>
            </div>

            <div className="hidden md:flex md:justify-end">
              <div className="relative flex h-64 w-64 items-center justify-center rounded-[2rem] border border-white/10 bg-white/[0.04] shadow-2xl">
                <div className="absolute inset-5 rounded-[1.5rem] border border-white/10" />

                <div className="flex h-32 w-32 items-center justify-center rounded-full bg-signal shadow-[0_0_70px_rgba(216,64,64,.3)]">
                  <MessageCircle size={54} strokeWidth={1.5} />
                </div>

                <div className="absolute -bottom-4 -start-7 rounded-2xl bg-white px-4 py-3 text-ink shadow-xl">
                  <div className="flex items-center gap-2 text-sm font-bold">
                    <Check size={17} className="text-signal" />
                    {t.official}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mx-auto grid max-w-7xl items-start gap-7 px-4 py-10 sm:px-6 lg:grid-cols-[minmax(0,1fr)_330px] lg:px-8 lg:py-14">
          <div
            id="complaint-form"
            className="rounded-3xl border border-stone-100 bg-white p-5 shadow-soft sm:p-8"
          >
            <div className="mb-8 flex flex-wrap items-start justify-between gap-4 border-b border-stone-100 pb-6">
              <div>
                <div className="mb-2 flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-signal">
                  <ClipboardList size={16} />
                  {t.step}
                </div>

                <h2 className="text-2xl font-black sm:text-3xl">
                  {t.formTitle}
                </h2>

                <p className="mt-2 text-sm leading-6 text-stone-500">
                  {t.formSub}
                </p>
              </div>

              <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-50 text-maroon">
                <FileText size={23} />
              </div>
            </div>

            <form onSubmit={handleSubmit} className="space-y-8">
              <section>
                <h3 className="mb-4 flex items-center gap-2 text-base font-extrabold">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-xs text-maroon">
                    01
                  </span>
                  {t.personal}
                </h3>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Field label={t.fullName} required>
                    <input
                      className="field"
                      autoComplete="name"
                      value={form.name}
                      onChange={(e) => update("name", e.target.value)}
                      placeholder={
                        rtl ? "أدخل اسمك بالكامل" : "Enter your full name"
                      }
                    />
                  </Field>

                  <Field label={t.phone} required>
                    <input
                      className="field"
                      type="tel"
                      autoComplete="tel"
                      value={form.phone}
                      onChange={(e) => update("phone", e.target.value)}
                      placeholder={
                        rtl ? "مثال: 01xxxxxxxxx" : "e.g. +20 1XXXXXXXXX"
                      }
                    />
                  </Field>

                  <div className="sm:col-span-2">
                    <Field label={t.email}>
                      <input
                        className="field"
                        type="email"
                        autoComplete="email"
                        value={form.email}
                        onChange={(e) => update("email", e.target.value)}
                        placeholder="name@example.com"
                      />
                    </Field>
                  </div>
                </div>
              </section>

              <section>
                <h3 className="mb-4 flex items-center gap-2 text-base font-extrabold">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-xs text-maroon">
                    02
                  </span>
                  {t.category}
                </h3>

                <Field label={t.category} required>
                  <div className="relative">
                    <select
                      className="field appearance-none pe-10"
                      value={category}
                      onChange={(e) => {
                        setCategory(e.target.value as Category | "");
                        setFormError("");
                      }}
                      required
                    >
                      <option value="">{t.choose}</option>
                      {categories.map((item) => (
                        <option key={item.id} value={item.id}>
                          {rtl ? item.ar : item.en}
                        </option>
                      ))}
                    </select>

                    <ChevronDown
                      size={17}
                      className={`pointer-events-none absolute top-1/2 -translate-y-1/2 text-stone-400 ${
                        rtl ? "left-4" : "right-4"
                      }`}
                    />
                  </div>
                </Field>

                {category === "other" && (
                  <div className="mt-4 rounded-2xl border border-red-100 bg-red-50/70 p-4">
                    <div className="flex items-start gap-3">
                      <div className="rounded-xl bg-white p-2 text-maroon">
                        <Sparkles size={20} />
                      </div>

                      <div className="flex-1">
                        <p className="font-bold">{t.otherRequired}</p>
                        <p className="mt-1 text-sm leading-6 text-stone-600">
                          {t.otherHelp}
                        </p>

                        <button
                          type="button"
                          onClick={openChat}
                          className="mt-3 inline-flex items-center gap-2 rounded-xl bg-maroon px-4 py-2.5 text-sm font-bold text-white transition hover:bg-signal"
                        >
                          <MessageCircle size={16} />
                          {t.chat}
                          <Arrow size={15} />
                        </button>
                      </div>
                    </div>
                  </div>
                )}
              </section>

              <section>
                <h3 className="mb-4 flex items-center gap-2 text-base font-extrabold">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-xs text-maroon">
                    03
                  </span>
                  {t.location}
                </h3>

                <div className="grid gap-4 sm:grid-cols-2">
                  
<Field label={t.area} required>
  <div className="relative">
    <input
      className="field"
      type="search"
      value={districtQuery}
      onChange={(e) => {
        setDistrictQuery(e.target.value);
        update("area", "");
      }}
      placeholder={
        rtl
          ? "ابحث عن الحي بالعربية أو الإنجليزية..."
          : "Search districts in Arabic or English..."
      }
      autoComplete="off"
      aria-autocomplete="list"
    />

    <ChevronDown
      size={17}
      className={`pointer-events-none absolute top-1/2 -translate-y-1/2 text-stone-400 ${
        rtl ? "left-4" : "right-4"
      }`}
    />
  </div>

  {districtQuery.trim() && (
    <div
      className="mt-2 max-h-52 overflow-y-auto rounded-xl border border-stone-200 bg-white shadow-sm"
      role="listbox"
    >
      {districts
        .filter((district) => {
          const query = districtQuery.trim().toLocaleLowerCase();

          return [district.ar, district.en, district.id].some(
            (label) => label.toLocaleLowerCase().includes(query)
          );
        })
        .map((district) => (
          <button
            key={district.id}
            type="button"
            role="option"
            aria-selected={form.area === district.id}
            onClick={() => {
              update("area", district.id);
              setDistrictQuery(rtl ? district.ar : district.en);
            }}
            className="block w-full px-4 py-3 text-start text-sm transition hover:bg-red-50"
          >
            <span className="block font-semibold">
              {rtl ? district.ar : district.en}
            </span>
            <span className="mt-1 block text-xs text-stone-400">
              {rtl ? district.en : district.ar}
            </span>
          </button>
        ))}

      {districts.filter((district) => {
        const query = districtQuery.trim().toLocaleLowerCase();
        return [district.ar, district.en, district.id].some(
          (label) => label.toLocaleLowerCase().includes(query)
        );
      }).length === 0 && (
        <p className="px-4 py-3 text-sm text-stone-500">
          {rtl ? "لا توجد أحياء مطابقة." : "No matching districts."}
        </p>
      )}
    </div>
  )}

  {!form.area && (
    <p className="mt-1 text-xs text-stone-500">
      {rtl ? "اختر حيًا من القائمة." : "Select a district from the list."}
    </p>
  )}
</Field>


                  <Field label={t.address} required>
                    <input
                      className="field"
                      value={form.address}
                      onChange={(e) => update("address", e.target.value)}
                      placeholder={t.addressPlaceholder}
                    />
                  </Field>
                </div>

                <p className="mt-3 flex items-center gap-2 text-xs leading-5 text-stone-500">
                  <MapPin size={14} className="shrink-0 text-signal" />
                  {rtl
                    ? "يرجى تحديد الموقع بأكبر قدر ممكن من الدقة."
                    : "Please describe the location as precisely as possible."}
                </p>
              </section>

              <section>
                <h3 className="mb-4 flex items-center gap-2 text-base font-extrabold">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-xs text-maroon">
                    04
                  </span>
                  {t.details}
                </h3>

                <div className="space-y-4">
                  <Field label={t.description} required>
                    <textarea
                      className="field min-h-32 resize-y"
                      value={form.description}
                      onChange={(e) =>
                        update("description", e.target.value)
                      }
                      placeholder={t.descriptionPlaceholder}
                      rows={4}
                    />
                  </Field>

                  <Field label={t.date} required>
                    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                      {[
                        ["today", t.today],
                        ["week", t.week],
                        ["month", t.month],
                        ["unknown", t.unknown],
                      ].map(([value, label]) => (
                        <button
                          key={value}
                          type="button"
                          onClick={() => update("onset", value)}
                          className={`rounded-xl border px-3 py-3 text-sm transition ${
                            form.onset === value
                              ? "border-maroon bg-red-50 font-bold text-maroon"
                              : "border-stone-200 text-stone-600 hover:border-red-200"
                          }`}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </Field>
                </div>
              </section>

              <section>
                <h3 className="mb-4 flex items-center gap-2 text-base font-extrabold">
                  <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-50 text-xs text-maroon">
                    05
                  </span>
                  {t.attachment}
                </h3>

                <label className="flex cursor-pointer flex-col items-center rounded-2xl border-2 border-dashed border-stone-200 bg-stone-50/70 px-5 py-7 text-center transition hover:border-signal hover:bg-red-50/40">
                  <span className="mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-maroon shadow-sm">
                    <UploadCloud size={23} />
                  </span>

                  <span className="text-sm font-bold">
                    {fileName || t.upload}
                  </span>

                  <span className="mt-1 text-xs text-stone-500">
                    {t.fileTypes}
                  </span>

                  <input
                    type="file"
                    accept=".png,.jpg,.jpeg,.pdf"
                    className="sr-only"
                    onChange={(e) =>
                      setFileName(e.target.files?.[0]?.name ?? "")
                    }
                  />
                </label>
              </section>

              <div className="border-t border-stone-100 pt-5">
                <label className="flex cursor-pointer items-start gap-3 text-sm leading-6 text-stone-600">
                  <input
                    type="checkbox"
                    checked={form.consent}
                    onChange={(e) => update("consent", e.target.checked)}
                    className="mt-1 h-4 w-4 accent-[#8E1616]"
                  />

                  <span>
                    {t.consent} <span className="text-signal">*</span>
                  </span>
                </label>

                {formError && (
                  <p
                    role="alert"
                    className="mt-4 rounded-xl border border-red-100 bg-red-50 px-4 py-3 text-sm font-semibold text-maroon"
                  >
                    {formError}
                  </p>
                )}

                <div className="mt-6 flex flex-col-reverse items-center justify-between gap-4 sm:flex-row">
                  <p className="text-xs text-stone-400">{t.required}</p>

                  <button
                    type="submit"
                    disabled={submitLoading}
                    className="flex w-full items-center justify-center gap-2 rounded-xl bg-signal px-7 py-3.5 font-bold text-white shadow-lg shadow-red-900/10 transition hover:-translate-y-0.5 hover:bg-maroon disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
                  >
                    {submitLoading
                      ? rtl
                        ? "جارٍ الإرسال..."
                        : "Submitting..."
                      : t.submit}
                    <Arrow size={17} />
                  </button>
                </div>
              </div>
            </form>
          </div>

          <aside className="space-y-5 lg:sticky lg:top-6">
            <div className="rounded-3xl bg-white p-6 shadow-soft">
              <div className="mb-5 flex h-11 w-11 items-center justify-center rounded-2xl bg-ink text-white">
                <ClipboardList size={22} />
              </div>

              <h2 className="text-xl font-black">{t.sideTitle}</h2>
              <p className="mt-2 text-sm text-stone-500">{t.sideSub}</p>

              <div className="mt-6 space-y-6">
                {[
                  {
                    n: "01",
                    title: t.step1,
                    sub: t.step1sub,
                    icon: FileText,
                  },
                  {
                    n: "02",
                    title: t.step2,
                    sub: t.step2sub,
                    icon: Headphones,
                  },
                  {
                    n: "03",
                    title: t.step3,
                    sub: t.step3sub,
                    icon: Check,
                  },
                ].map(({ n, title, sub, icon: Icon }, i) => (
                  <div className="flex gap-3" key={n}>
                    <div className="relative flex flex-col items-center">
                      <div
                        className={`z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl ${
                          i === 0
                            ? "bg-red-50 text-maroon"
                            : "bg-stone-100 text-stone-600"
                        }`}
                      >
                        <Icon size={19} />
                      </div>

                      {i < 2 && (
                        <div className="absolute top-11 h-10 border-s border-dashed border-stone-200" />
                      )}
                    </div>

                    <div className="pb-2">
                      <p className="font-bold">{title}</p>
                      <p className="mt-1 text-sm leading-6 text-stone-500">
                        {sub}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="overflow-hidden rounded-3xl bg-maroon p-6 text-white">
              <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-white/10">
                <MessageCircle size={23} />
              </div>

              <h3 className="text-lg font-black">{t.noteTitle}</h3>
              <p className="mt-2 text-sm leading-6 text-white/75">
                {t.note}
              </p>

              <button
                type="button"
                onClick={openChat}
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-extrabold text-maroon transition hover:bg-red-50"
              >
                <Sparkles size={17} />
                {t.chat}
                <Arrow size={16} />
              </button>
            </div>

            <div className="flex items-start gap-3 rounded-2xl border border-stone-200 bg-white/60 p-4 text-xs leading-5 text-stone-500">
              <ShieldCheck size={18} className="shrink-0 text-maroon" />
              {rtl
                ? "لا تشارك معلومات حساسة لا تحتاجها معالجة الشكوى."
                : "Avoid sharing sensitive information that is not needed to process your complaint."}
            </div>
          </aside>
        </section>
      </main>

      <footer className="border-t border-stone-200 bg-white">
        <div className="mx-auto flex max-w-7xl flex-col gap-3 px-4 py-6 text-xs text-stone-500 sm:flex-row sm:items-center sm:justify-between sm:px-6 lg:px-8">
          <p>{t.footer}</p>

          <div className="flex gap-5">
            <a href="#privacy" className="hover:text-maroon">
              {t.privacy}
            </a>
            <a href="#terms" className="hover:text-maroon">
              {t.terms}
            </a>
          </div>
        </div>
      </footer>

      {chatOpen && (
        <div
          className="fixed inset-0 z-50 flex items-end justify-center bg-ink/50 p-0 backdrop-blur-sm sm:items-center sm:p-5"
          role="dialog"
          aria-modal="true"
          aria-label={t.chatbotTitle}
        >
          <div className="flex max-h-[90vh] w-full max-w-lg flex-col overflow-hidden rounded-t-3xl bg-white shadow-2xl sm:rounded-3xl">
            <div className="flex items-center justify-between bg-ink px-5 py-4 text-white">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-signal">
                  <Sparkles size={21} />
                </div>

                <div>
                  <h2 className="font-extrabold">{t.chatbotTitle}</h2>
                  <p className="mt-0.5 text-xs text-white/60">
                    {rtl ? "متاح لمساعدتك" : "Here to help"}
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={() => setChatOpen(false)}
                className="rounded-lg p-2 text-white/70 transition hover:bg-white/10 hover:text-white"
                aria-label={t.close}
              >
                <X size={20} />
              </button>
            </div>

            <div className="flex-1 space-y-4 overflow-y-auto bg-[#FAF9F9] p-5">
              {chatMessages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${
                    msg.from === "user"
                      ? rtl
                        ? "justify-start"
                        : "justify-end"
                      : rtl
                        ? "justify-end"
                        : "justify-start"
                  }`}
                >
                  <div
                    className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-6 ${
                      msg.from === "user"
                        ? "bg-maroon text-white"
                        : "border border-stone-100 bg-white text-stone-700 shadow-sm"
                    }`}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}

              {chatLoading && (
                <div className="text-sm text-stone-500" role="status">
                  {rtl ? "المساعد يكتب..." : "Assistant is typing..."}
                </div>
              )}

              {chatReadyForReview && (
                <div className="flex justify-center pt-1">
                  <button
                    type="button"
                    onClick={useChatDetails}
                    className="inline-flex items-center gap-2 rounded-xl border border-red-100 bg-red-50 px-4 py-2.5 text-sm font-bold text-maroon hover:bg-red-100"
                  >
                    <Check size={16} />
                    {t.useDetails}
                  </button>
                </div>
              )}
            </div>

            <div className="border-t border-stone-100 bg-white p-4">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  void sendChat();
                }}
                className="flex items-center gap-2"
              >
                <input
                  className="field"
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  placeholder={t.chatPlaceholder}
                />

                <button
                  type="submit"
                  disabled={chatLoading || !chatInput.trim()}
                  className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-signal text-white transition hover:bg-maroon disabled:cursor-not-allowed disabled:opacity-50"
                  aria-label={t.send}
                >
                  <Send size={18} />
                </button>
              </form>

              <p className="mt-2 text-center text-[11px] text-stone-400">
                {t.chatHint}
              </p>
            </div>
          </div>
        </div>
      )}

      {showSuccess && (
        <div
          className="fixed inset-0 z-[60] flex items-center justify-center bg-ink/50 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
        >
          <div className="w-full max-w-md rounded-3xl bg-white p-7 text-center shadow-2xl">
            <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-red-50 text-maroon">
              <Check size={30} />
            </div>

            <h2 className="mt-5 text-2xl font-black">
              {t.successTitle}
            </h2>

            <p className="mt-3 text-sm leading-6 text-stone-500">
              {t.successText}
            </p>

            <div className="mt-5 rounded-2xl bg-stone-50 p-4 text-start text-sm">
              <p className="mb-2 font-bold">{t.summary}</p>

              {referenceNumber && (
                <p className="mb-2 rounded-lg bg-red-50 p-2 font-bold text-maroon">
                  {rtl ? "رقم المرجع" : "Reference number"}:{" "}
                  {referenceNumber}
                </p>
              )}

              <p className="text-stone-600">
                {rtl ? "الاسم" : "Name"}: {form.name}
              </p>

              <p className="mt-1 text-stone-600">
                {rtl ? "النوع" : "Category"}:{" "}
                {selectedCategory
                  ? rtl
                    ? selectedCategory.ar
                    : selectedCategory.en
                  : "—"}
              </p>

              <p className="mt-1 text-stone-600">
                {rtl ? "الموقع" : "Location"}: {form.area} — {form.address}
              </p>
            </div>

            <button
              type="button"
              onClick={() => setShowSuccess(false)}
              className="mt-6 w-full rounded-xl bg-maroon px-5 py-3 font-bold text-white hover:bg-signal"
            >
              {t.successClose}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-bold text-stone-700">
        {label}
        {required && <span className="ms-1 text-signal">*</span>}
      </span>
      {children}
    </label>
  );
}