"use client";

import { FormEvent, useState } from "react";

export default function EnquiryForm({ propertyId }: { propertyId: string }) {
  const [status, setStatus] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [consent, setConsent] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!consent || status === "sending") return;
    const data = new FormData(event.currentTarget);
    const api = process.env.NEXT_PUBLIC_AUREL_API_URL;
    if (!api) { setStatus("error"); return; }
    setStatus("sending");
    try {
      const response = await fetch(`${api.replace(/\/$/, "")}/public/properties/${encodeURIComponent(propertyId)}/enquiries`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({
          name: String(data.get("name") ?? ""),
          email: String(data.get("email") ?? ""),
          message: String(data.get("message") ?? ""),
          consent_recorded: consent,
        }),
      });
      setStatus(response.ok ? "sent" : "error");
      if (response.ok) event.currentTarget.reset();
    } catch {
      setStatus("error");
    }
  }

  return (
    <form className="enquiry-form" onSubmit={submit}>
      <label>Your name<input name="name" required minLength={2} maxLength={120} autoComplete="name"/></label>
      <label>Email address<input name="email" type="email" required maxLength={254} autoComplete="email"/></label>
      <label>Your message<textarea name="message" required minLength={10} maxLength={4000} rows={4}/></label>
      <label className="consent-row"><input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)}/>I agree to be contacted about this enquiry and understand my details will be used to respond.</label>
      <button type="submit" disabled={!consent || status === "sending"}>{status === "sending" ? "Sending…" : "Send private enquiry"} <span>↗</span></button>
      {status === "sent" && <p className="form-status success">Your enquiry has been received.</p>}
      {status === "error" && <p className="form-status">The enquiry could not be sent. Please try again later.</p>}
    </form>
  );
}
