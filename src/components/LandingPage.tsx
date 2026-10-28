
import { useState } from "react";

type LandingPageProps = {
  onSelectResident: () => void;
  onSelectInvestor: () => void;
  onSelectGovernment: () => void;
};

export default function LandingPage({
  onSelectResident,
  onSelectInvestor,
  onSelectGovernment,
}: LandingPageProps) {
  const [lang, setLang] = useState<"en" | "ar">("en");
  const ar = lang === "ar";

  const copy = {
    brand: "ACUD",
    tagline: ar
      ? "العاصمة الجديدة، مستقبل أفضل"
      : "NEW ADMINISTRATIVE CAPITAL",
    eyebrow: ar
      ? "عاصمتنا، مسؤوليتنا المشتركة"
      : "YOUR CAPITAL. YOUR VOICE.",
    title: ar
      ? "معًا نبني عاصمة أفضل"
      : "Together, we build a better capital.",
    description: ar
      ? "بوابتك الرقمية للتواصل مع شركة العاصمة الإدارية للتنمية العمرانية، وتقديم الشكاوى والاستفسارات."
      : "Your digital gateway to ACUD for submitting complaints, inquiries, and service requests.",
    choose: ar ? "كيف يمكننا مساعدتك؟" : "How can we help you?",
    residents: ar ? "السكان" : "Residents",
    residentDesc: ar
      ? "قدّم شكوى بشأن الطرق أو الإنارة أو النظافة أو المياه أو مواقف السيارات أو الخدمات داخل الحي."
      : "Report issues with roads, lighting, waste, water, parking, and neighborhood services.",
    residentButton: ar ? "تقديم شكوى" : "Submit a complaint",
    investors: ar ? "المستثمرون" : "Investors",
    investorDesc: ar
      ? "تواصل بشأن الفرص الاستثمارية والمشروعات والاستفسارات والخدمات المتعلقة بالمستثمرين."
      : "Contact us about investment opportunities, projects, and investor-related inquiries.",
    investorButton: ar ? "خدمات المستثمرين" : "Investor services",
    government: ar ? "الخدمات الحكومية" : "Government Services",
    governmentDesc: ar
      ? "استكشف الخدمات الحكومية والإجراءات الرقمية، واحصل على المعلومات اللازمة للاستفسارات والخدمات المتاحة."
      : "Explore government services and digital procedures, and find information about available services and inquiries.",
    governmentButton: ar ? "استعراض الخدمات الحكومية" : "Explore government services",
    footer: ar
      ? "شركة العاصمة الإدارية للتنمية العمرانية · مصر"
      : "Administrative Capital for Urban Development · Egypt",
    servicesLabel: ar ? "الخدمات الرقمية" : "ACUD DIGITAL SERVICES",
    servicesHint: ar
      ? "اختر الفئة المناسبة للمتابعة إلى الخدمة المطلوبة."
      : "Choose the option that best describes your needs.",
    future: ar ? "المستقبل يبدأ هنا" : "THE FUTURE STARTS HERE",
  };

  return (
    <main
      dir={ar ? "rtl" : "ltr"}
      className="min-h-screen bg-[#EEEEEE] text-[#1D1616]"
    >
      <header className="bg-[#1D1616] text-white">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-5 py-5 md:px-10">
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-[#8E1616] text-xl font-black">
              A
            </div>
            <div>
              <div className="text-xl font-bold tracking-widest">
                {copy.brand}
              </div>
              <div className="text-[10px] tracking-wider text-gray-300">
                {copy.tagline}
              </div>
            </div>
          </div>

          <button
            onClick={() => setLang(ar ? "en" : "ar")}
            className="rounded-lg border border-white/30 px-4 py-2 text-sm transition hover:bg-white/10"
            aria-label={ar ? "Switch to English" : "التبديل إلى العربية"}
          >
            {ar ? "English" : "العربية"}
          </button>
        </nav>
      </header>

      <section className="relative overflow-hidden bg-[#1D1616] text-white">
        <div className="pointer-events-none absolute -right-24 -top-24 h-80 w-80 rounded-full bg-[#8E1616]/40 blur-3xl" />

        <div className="relative mx-auto grid max-w-7xl items-center gap-10 px-5 py-16 md:grid-cols-2 md:px-10 md:py-24">
          <div>
            <p className="mb-5 text-sm font-semibold uppercase tracking-[0.2em] text-[#D84040]">
              {copy.eyebrow}
            </p>

            <h1 className="max-w-2xl text-4xl font-extrabold leading-tight md:text-6xl">
              {copy.title}
            </h1>

            <p className="mt-6 max-w-xl text-base leading-8 text-gray-300 md:text-lg">
              {copy.description}
            </p>

            <button
              onClick={() =>
                document.getElementById("services")?.scrollIntoView({
                  behavior: "smooth",
                })
              }
              className="mt-8 rounded-lg bg-[#D84040] px-6 py-3 font-semibold text-white transition hover:bg-[#b92e2e]"
            >
              {copy.choose} ↓
            </button>
          </div>

          <div className="relative">
            <div className="flex aspect-[5/4] items-center justify-center overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-[#8E1616] via-[#4a2424] to-[#242020] p-8">
              <div className="text-center">
                <div className="text-7xl font-black tracking-widest text-white/90 md:text-9xl">
                  ACUD
                </div>
                <div className="mx-auto mt-5 h-1 w-24 rounded-full bg-[#D84040]" />
                <p className="mt-5 text-sm tracking-[0.25em] text-white/70">
                  {copy.future}
                </p>
              </div>
            </div>

            <div className="absolute -bottom-4 -left-4 h-20 w-20 rounded-xl border border-[#D84040]/50" />
          </div>
        </div>
      </section>

      <section
        id="services"
        className="mx-auto max-w-7xl px-5 py-16 md:px-10 md:py-20"
      >
        <div className="mx-auto mb-10 max-w-2xl text-center">
          <p className="text-sm font-bold uppercase tracking-widest text-[#8E1616]">
            {copy.servicesLabel}
          </p>

          <h2 className="mt-3 text-3xl font-extrabold md:text-4xl">
            {copy.choose}
          </h2>

          <p className="mt-3 text-gray-600">{copy.servicesHint}</p>
        </div>

        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-2">
          {/* Residents */}
          <article className="group flex flex-col rounded-2xl border border-gray-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:border-[#8E1616]/40 hover:shadow-xl md:p-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#8E1616]/10 text-[#8E1616]">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                className="h-7 w-7"
                aria-hidden="true"
              >
                <path d="M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                <circle cx="10" cy="7" r="4" />
                <path d="M20 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
            </div>

            <h3 className="mt-6 text-2xl font-bold">{copy.residents}</h3>

            <p className="mt-4 flex-1 leading-7 text-gray-600">
              {copy.residentDesc}
            </p>

            <button
              onClick={onSelectResident}
              className="mt-8 flex w-full items-center justify-center gap-2 rounded-lg bg-[#8E1616] px-5 py-4 font-semibold text-white transition hover:bg-[#6f1010]"
            >
              {copy.residentButton}
              <span aria-hidden="true">{ar ? "←" : "→"}</span>
            </button>
          </article>

          {/* Investors */}
          <article className="group flex flex-col rounded-2xl border border-gray-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:border-[#D84040]/50 hover:shadow-xl md:p-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#D84040]/10 text-[#8E1616]">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                className="h-7 w-7"
                aria-hidden="true"
              >
                <path d="M3 21h18M5 21V7l8-4v18M19 21V11l-6-4" />
                <path d="M8 9v.01M8 12v.01M8 15v.01M8 18v.01M16 13v.01M16 16v.01M16 19v.01" />
              </svg>
            </div>

            <h3 className="mt-6 text-2xl font-bold">{copy.investors}</h3>

            <p className="mt-4 flex-1 leading-7 text-gray-600">
              {copy.investorDesc}
            </p>

            <button
              onClick={onSelectInvestor}
              className="mt-8 flex w-full items-center justify-center gap-2 rounded-lg bg-[#1D1616] px-5 py-4 font-semibold text-white transition hover:bg-[#3c2929]"
            >
              {copy.investorButton}
              <span aria-hidden="true">{ar ? "←" : "→"}</span>
            </button>
          </article>

          {/* Government Services 
          <article className="group flex flex-col rounded-2xl border border-gray-200 bg-white p-7 shadow-sm transition hover:-translate-y-1 hover:border-[#8E1616]/40 hover:shadow-xl md:p-8">
            <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-[#8E1616]/10 text-[#8E1616]">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-7 w-7"
                aria-hidden="true"
              >
                <path d="M3 10h18L12 4 3 10Z" />
                <path d="M5 10v9M9 10v9M15 10v9M19 10v9M3 21h18M2 19h20" />
              </svg>
            </div>

            <h3 className="mt-6 text-2xl font-bold">
              {copy.government}
            </h3>

            <p className="mt-4 flex-1 leading-7 text-gray-600">
              {copy.governmentDesc}
            </p>

            <button
              onClick={onSelectGovernment}
              className="mt-8 flex w-full items-center justify-center gap-2 rounded-lg bg-[#8E1616] px-5 py-4 font-semibold text-white transition hover:bg-[#6f1010]"
            >
              {copy.governmentButton}
              <span aria-hidden="true">{ar ? "←" : "→"}</span>
            </button>
          </article>*/}
        </div>
      </section>

      <footer className="bg-[#1D1616] px-5 py-7 text-center text-sm text-gray-300">
        <p>{copy.footer}</p>
        <p className="mt-2 text-xs text-gray-500">
          © {new Date().getFullYear()} ACUD
        </p>
      </footer>
    </main>
  );
}
