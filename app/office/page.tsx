"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { authClient } from "@/lib/auth/client";

type User = { id: string; name?: string | null; email?: string | null };
type Organization = { id: string; name: string; slug?: string };
type Property = {
  id: string;
  title: string;
  city: string;
  country_code: string;
  property_type: string;
  verification_state: string;
  visibility: string;
  evidence_count?: number;
};
type ApiResult = { items?: Property[]; item?: Property; error?: string };

const client = authClient as any;
const apiBase = (process.env.NEXT_PUBLIC_AUREL_API_URL ?? "").replace(/\/$/, "");

export default function OfficePage() {
  const [user, setUser] = useState<User | null>(null);
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [organizationId, setOrganizationId] = useState("");
  const [organizationName, setOrganizationName] = useState("");
  const [properties, setProperties] = useState<Property[]>([]);
  const [reviewQueue, setReviewQueue] = useState<Property[]>([]);
  const [selectedProperty, setSelectedProperty] = useState("");
  const [mode, setMode] = useState<"sign-in" | "sign-up" | "verify">("sign-in");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [otp, setOtp] = useState("");
  const [status, setStatus] = useState("");
  const [busy, setBusy] = useState(false);
  const [propertyDraft, setPropertyDraft] = useState({
    title: "", description: "", country_code: "PT", city: "", property_type: "apartment", currency: "EUR", asking_price_minor: ""
  });
  const [evidenceDraft, setEvidenceDraft] = useState({
    evidence_type: "ownership", note: "", source_url: "", reference_code: "", observed_at: new Date().toISOString().slice(0, 10)
  });

  const selectedOrg = useMemo(() => organizations.find((item) => item.id === organizationId), [organizations, organizationId]);

  async function refreshSession() {
    try {
      const result = await client.getSession();
      const currentUser = result?.data?.user ?? null;
      setUser(currentUser);
      if (!currentUser) {
        setOrganizations([]);
        setOrganizationId("");
        setProperties([]);
        setReviewQueue([]);
        return;
      }
      const orgResult = await client.organization.list();
      const list = Array.isArray(orgResult?.data) ? orgResult.data : (orgResult?.data?.organizations ?? []);
      setOrganizations(list);
      if (list.length === 1) {
        setOrganizationId(list[0].id);
        await loadWorkspace(list[0].id);
      }
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось проверить сессию");
    }
  }

  useEffect(() => { void refreshSession(); }, []);

  async function request(path: string, method = "GET", body?: unknown, orgId = organizationId) {
    if (!apiBase) throw new Error("API staging не подключён");
    const tokenResult = await client.token();
    const token = tokenResult?.data?.token;
    if (!token) throw new Error("Сессия истекла. Войдите повторно.");
    const response = await fetch(apiBase + path, {
      method,
      headers: {
        Authorization: "Bearer " + token,
        "X-Aurel-Organization-Id": orgId,
        ...(body ? { "Content-Type": "application/json" } : {})
      },
      body: body ? JSON.stringify(body) : undefined,
      cache: "no-store"
    });
    const data = await response.json().catch(() => ({})) as ApiResult;
    if (!response.ok) throw new Error(data.error ?? "Ошибка запроса: " + response.status);
    return data;
  }

  async function loadWorkspace(orgId: string) {
    if (!orgId) return;
    setBusy(true);
    try {
      const result = await request("/api/v1/properties", "GET", undefined, orgId);
      setProperties(result.items ?? []);
      try {
        const queue = await request("/api/v1/review-queue", "GET", undefined, orgId);
        setReviewQueue(queue.items ?? []);
      } catch {
        setReviewQueue([]);
      }
      setStatus("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось загрузить объекты");
    } finally {
      setBusy(false);
    }
  }

  async function signIn(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const result = await client.signIn.email({ email, password });
      if (result?.error) throw new Error(result.error.message ?? "Не удалось войти");
      await refreshSession();
      setStatus("Вход выполнен");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ошибка входа");
    } finally {
      setBusy(false);
    }
  }

  async function signUp(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const result = await client.signUp.email({ email, password, name: fullName });
      if (result?.error) throw new Error(result.error.message ?? "Не удалось создать аккаунт");
      setMode("verify");
      setStatus("На почту отправлен код подтверждения.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ошибка регистрации");
    } finally {
      setBusy(false);
    }
  }

  async function verifyEmail(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      const verify = client.emailOtp?.verifyEmail;
      if (typeof verify !== "function") throw new Error("Проверка OTP не поддерживается текущей конфигурацией Neon Auth");
      const result = await verify({ email, otp });
      if (result?.error) throw new Error(result.error.message ?? "Неверный код");
      const login = await client.signIn.email({ email, password });
      if (login?.error) throw new Error(login.error.message ?? "Почта подтверждена, но вход не выполнен");
      await refreshSession();
      setStatus("Почта подтверждена");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось подтвердить почту");
    } finally {
      setBusy(false);
    }
  }

  async function createOrganization(event: FormEvent) {
    event.preventDefault();
    const name = organizationName.trim();
    if (name.length < 2) return setStatus("Укажите название агентства");
    setBusy(true);
    try {
      const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 48) || "aurel-agency";
      const result = await client.organization.create({ name, slug });
      if (result?.error) throw new Error(result.error.message ?? "Не удалось создать агентство");
      const organization = result?.data?.organization ?? result?.data;
      if (!organization?.id) throw new Error("Neon Auth не вернул идентификатор агентства");
      const next = [...organizations, organization];
      setOrganizations(next);
      setOrganizationId(organization.id);
      await loadWorkspace(organization.id);
      setStatus("Рабочее пространство создано");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ошибка создания агентства");
    } finally {
      setBusy(false);
    }
  }

  async function createProperty(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    try {
      await request("/api/v1/properties", "POST", {
        ...propertyDraft,
        asking_price_minor: propertyDraft.asking_price_minor || null
      });
      setPropertyDraft({ title: "", description: "", country_code: "PT", city: "", property_type: "apartment", currency: "EUR", asking_price_minor: "" });
      await loadWorkspace(organizationId);
      setStatus("Объект сохранён как непроверенный");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось сохранить объект");
    } finally {
      setBusy(false);
    }
  }

  async function addEvidence(event: FormEvent) {
    event.preventDefault();
    if (!selectedProperty) return setStatus("Сначала выберите объект");
    setBusy(true);
    try {
      await request("/api/v1/properties/" + selectedProperty + "/evidence", "POST", {
        ...evidenceDraft,
        source_url: evidenceDraft.source_url || null,
        reference_code: evidenceDraft.reference_code || null,
        observed_at: new Date(evidenceDraft.observed_at).toISOString()
      });
      await loadWorkspace(organizationId);
      setStatus("Подтверждающий материал добавлен");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось добавить материал");
    } finally {
      setBusy(false);
    }
  }

  async function submitProperty(id: string) {
    setBusy(true);
    try {
      await request("/api/v1/properties/" + id + "/submit", "POST");
      await loadWorkspace(organizationId);
      setStatus("Объект передан на независимую проверку");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось отправить объект");
    } finally {
      setBusy(false);
    }
  }

  async function reviewProperty(id: string, action: "verify" | "reject") {
    setBusy(true);
    try {
      await request("/api/v1/properties/" + id + "/review", "POST", { action, publish: action === "verify" });
      await loadWorkspace(organizationId);
      setStatus(action === "verify" ? "Объект проверен" : "Объект отклонён");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Не удалось завершить проверку");
    } finally {
      setBusy(false);
    }
  }

  async function signOut() {
    await client.signOut();
    setUser(null);
    setOrganizations([]);
    setOrganizationId("");
    setProperties([]);
    setReviewQueue([]);
  }

  if (!user) {
    return (
      <main className="min-h-screen bg-[#f6f4ef] px-5 py-12 text-[#1d2724]">
        <section className="mx-auto max-w-xl rounded-3xl border border-[#d9d5cc] bg-white p-8 shadow-sm">
          <a href="/" className="text-sm text-[#66716b]">← AUREL</a>
          <p className="mt-8 text-xs uppercase tracking-[0.24em] text-[#9a7954]">AUREL · Agency access</p>
          <h1 className="mt-3 text-3xl font-semibold">Рабочее пространство агентства</h1>
          <p className="mt-3 text-sm leading-6 text-[#66716b]">Вход защищён Neon Auth. Доступ к объектам определяется членством в агентстве, а не ролью из браузера.</p>
          {mode === "verify" ? (
            <form onSubmit={verifyEmail} className="mt-8 space-y-4">
              <label className="block text-sm">Код из письма<input className="mt-2 w-full rounded-xl border p-3" value={otp} onChange={(e) => setOtp(e.target.value)} required /></label>
              <button disabled={busy} className="w-full rounded-xl bg-[#20332c] p-3 text-white">Подтвердить почту</button>
            </form>
          ) : (
            <form onSubmit={mode === "sign-in" ? signIn : signUp} className="mt-8 space-y-4">
              {mode === "sign-up" && <label className="block text-sm">Имя<input className="mt-2 w-full rounded-xl border p-3" value={fullName} onChange={(e) => setFullName(e.target.value)} required /></label>}
              <label className="block text-sm">Email<input type="email" className="mt-2 w-full rounded-xl border p-3" value={email} onChange={(e) => setEmail(e.target.value)} required /></label>
              <label className="block text-sm">Пароль<input type="password" minLength={8} className="mt-2 w-full rounded-xl border p-3" value={password} onChange={(e) => setPassword(e.target.value)} required /></label>
              <button disabled={busy} className="w-full rounded-xl bg-[#20332c] p-3 text-white">{mode === "sign-in" ? "Войти" : "Создать аккаунт"}</button>
            </form>
          )}
          {mode !== "verify" && <button className="mt-5 text-sm underline" onClick={() => setMode(mode === "sign-in" ? "sign-up" : "sign-in")}>{mode === "sign-in" ? "Создать аккаунт агентства" : "Уже есть аккаунт? Войти"}</button>}
          {status && <p className="mt-5 rounded-xl bg-[#f4f0e8] p-3 text-sm">{status}</p>}
        </section>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#f6f4ef] px-5 py-10 text-[#1d2724]">
      <div className="mx-auto max-w-6xl">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div><a href="/" className="text-sm text-[#66716b]">← AUREL</a><p className="mt-4 text-xs uppercase tracking-[0.24em] text-[#9a7954]">Agency workspace</p><h1 className="mt-2 text-3xl font-semibold">Управление объектами</h1><p className="mt-2 text-sm text-[#66716b]">{user.email}</p></div>
          <button onClick={signOut} className="rounded-xl border border-[#d9d5cc] bg-white px-4 py-2 text-sm">Выйти</button>
        </header>
        {status && <p className="mt-6 rounded-xl bg-white p-4 text-sm shadow-sm">{status}</p>}
        <section className="mt-8 rounded-2xl border border-[#d9d5cc] bg-white p-5">
          <h2 className="font-semibold">Агентство</h2>
          {organizations.length > 0 ? (
            <select className="mt-3 w-full max-w-md rounded-xl border p-3" value={organizationId} onChange={(e) => { setOrganizationId(e.target.value); void loadWorkspace(e.target.value); }}>
              <option value="">Выберите агентство</option>
              {organizations.map((org) => <option key={org.id} value={org.id}>{org.name}</option>)}
            </select>
          ) : (
            <form onSubmit={createOrganization} className="mt-3 flex flex-wrap gap-3">
              <input className="min-w-0 flex-1 rounded-xl border p-3" placeholder="Название агентства" value={organizationName} onChange={(e) => setOrganizationName(e.target.value)} required />
              <button disabled={busy} className="rounded-xl bg-[#20332c] px-5 py-3 text-white">Создать пространство</button>
            </form>
          )}
          {selectedOrg && <p className="mt-2 text-xs text-[#66716b]">{selectedOrg.slug ?? selectedOrg.id}</p>}
        </section>
        {organizationId && <>
          <section className="mt-8 grid gap-6 lg:grid-cols-2">
            <form onSubmit={createProperty} className="rounded-2xl border border-[#d9d5cc] bg-white p-5">
              <h2 className="text-lg font-semibold">Новый объект</h2>
              <div className="mt-4 grid gap-3">
                <input className="rounded-xl border p-3" placeholder="Название объекта" value={propertyDraft.title} onChange={(e) => setPropertyDraft({ ...propertyDraft, title: e.target.value })} required minLength={5} />
                <textarea className="min-h-28 rounded-xl border p-3" placeholder="Описание и существенные характеристики" value={propertyDraft.description} onChange={(e) => setPropertyDraft({ ...propertyDraft, description: e.target.value })} required minLength={20} />
                <div className="grid grid-cols-2 gap-3">
                  <input className="rounded-xl border p-3" placeholder="Страна ISO-2" value={propertyDraft.country_code} onChange={(e) => setPropertyDraft({ ...propertyDraft, country_code: e.target.value.toUpperCase() })} required />
                  <input className="rounded-xl border p-3" placeholder="Город" value={propertyDraft.city} onChange={(e) => setPropertyDraft({ ...propertyDraft, city: e.target.value })} required />
                  <select className="rounded-xl border p-3" value={propertyDraft.property_type} onChange={(e) => setPropertyDraft({ ...propertyDraft, property_type: e.target.value })}><option value="apartment">Апартаменты</option><option value="house">Дом</option><option value="villa">Вилла</option><option value="penthouse">Пентхаус</option><option value="land">Земля</option><option value="commercial">Коммерческий</option><option value="other">Другое</option></select>
                  <input className="rounded-xl border p-3" placeholder="Валюта ISO-4217" value={propertyDraft.currency} onChange={(e) => setPropertyDraft({ ...propertyDraft, currency: e.target.value.toUpperCase() })} required />
                </div>
                <input className="rounded-xl border p-3" inputMode="numeric" placeholder="Цена в минимальных единицах валюты" value={propertyDraft.asking_price_minor} onChange={(e) => setPropertyDraft({ ...propertyDraft, asking_price_minor: e.target.value.replace(/[^0-9]/g, "") })} />
                <button disabled={busy || !organizationId} className="rounded-xl bg-[#20332c] p-3 text-white">Сохранить объект</button>
              </div>
            </form>
            <form onSubmit={addEvidence} className="rounded-2xl border border-[#d9d5cc] bg-white p-5">
              <h2 className="text-lg font-semibold">Подтверждающие материалы</h2>
              <p className="mt-1 text-sm text-[#66716b]">Материалы добавляются в неизменяемый журнал объекта.</p>
              <div className="mt-4 grid gap-3">
                <select className="rounded-xl border p-3" value={selectedProperty} onChange={(e) => setSelectedProperty(e.target.value)}><option value="">Выберите объект</option>{properties.map((item) => <option key={item.id} value={item.id}>{item.title}</option>)}</select>
                <select className="rounded-xl border p-3" value={evidenceDraft.evidence_type} onChange={(e) => setEvidenceDraft({ ...evidenceDraft, evidence_type: e.target.value })}><option value="ownership">Право собственности</option><option value="mandate">Мандат агентства</option><option value="source_listing">Источник объявления</option><option value="price_confirmation">Подтверждение цены</option><option value="media_rights">Права на медиа</option><option value="inspection">Осмотр</option><option value="other">Другое</option></select>
                <input className="rounded-xl border p-3" placeholder="HTTPS-ссылка на источник (необязательно)" value={evidenceDraft.source_url} onChange={(e) => setEvidenceDraft({ ...evidenceDraft, source_url: e.target.value })} />
                <input className="rounded-xl border p-3" placeholder="Код документа / референс (необязательно)" value={evidenceDraft.reference_code} onChange={(e) => setEvidenceDraft({ ...evidenceDraft, reference_code: e.target.value })} />
                <textarea className="min-h-24 rounded-xl border p-3" placeholder="Что именно подтверждает материал" value={evidenceDraft.note} onChange={(e) => setEvidenceDraft({ ...evidenceDraft, note: e.target.value })} required minLength={10} />
                <input type="date" className="rounded-xl border p-3" value={evidenceDraft.observed_at} onChange={(e) => setEvidenceDraft({ ...evidenceDraft, observed_at: e.target.value })} required />
                <button disabled={busy || !selectedProperty} className="rounded-xl border border-[#20332c] p-3">Добавить материал</button>
              </div>
            </form>
          </section>
          <section className="mt-8 rounded-2xl border border-[#d9d5cc] bg-white p-5">
            <div className="flex flex-wrap items-center justify-between gap-3"><h2 className="text-lg font-semibold">Объекты агентства</h2><button onClick={() => void loadWorkspace(organizationId)} className="text-sm underline">Обновить</button></div>
            {busy && <p className="mt-3 text-sm text-[#66716b]">Загрузка…</p>}
            {properties.length === 0 ? <p className="mt-4 text-sm text-[#66716b]">Объектов пока нет. Добавьте объект и приложите подтверждающие материалы.</p> : <div className="mt-4 divide-y">{properties.map((item) => <article key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div><h3 className="font-medium">{item.title}</h3><p className="mt-1 text-sm text-[#66716b]">{item.city}, {item.country_code} · {item.property_type} · {item.verification_state} · материалов: {item.evidence_count ?? 0}</p></div><button onClick={() => void submitProperty(item.id)} disabled={busy || item.verification_state === "in_review" || item.verification_state === "verified"} className="rounded-xl border px-4 py-2 text-sm">Передать на проверку</button></article>)}</div>}
          </section>
          {reviewQueue.length > 0 && <section className="mt-8 rounded-2xl border border-[#d9d5cc] bg-white p-5"><h2 className="text-lg font-semibold">Очередь независимой проверки</h2><div className="mt-4 divide-y">{reviewQueue.map((item) => <article key={item.id} className="flex flex-wrap items-center justify-between gap-3 py-4"><div><h3 className="font-medium">{item.title}</h3><p className="text-sm text-[#66716b]">{item.city}, {item.country_code}</p></div><div className="flex gap-2"><button onClick={() => void reviewProperty(item.id, "reject")} disabled={busy} className="rounded-xl border px-3 py-2 text-sm">Отклонить</button><button onClick={() => void reviewProperty(item.id, "verify")} disabled={busy} className="rounded-xl bg-[#20332c] px-3 py-2 text-sm text-white">Проверить и опубликовать</button></div></article>)}</div></section>}
        </>}
        <p className="mt-8 text-xs leading-5 text-[#78827c]">Публикация возможна только после независимой проверки и наличия подтверждающих материалов. Удаление доказательств и истории аудита недоступно.</p>
      </div>
    </main>
  );
}
