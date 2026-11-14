import Link from "next/link";
import { notFound } from "next/navigation";
import EnquiryForm from "./enquiry-form";

export const dynamic = "force-dynamic";

type Property = {
  id: string;
  title: string;
  description: string;
  country_code: string;
  city: string;
  property_type: string;
  currency: string;
  asking_price_minor: number | null;
};

async function loadProperty(id: string): Promise<Property | null> {
  const base = process.env.AUREL_API_URL;
  if (!base) return null;
  try {
    const response = await fetch(`${base.replace(/\/$/, "")}/public/properties/${encodeURIComponent(id)}`, { cache: "no-store" });
    if (!response.ok) return null;
    return (await response.json()) as Property;
  } catch {
    return null;
  }
}

function formatPrice(value: number | null, currency: string): string {
  if (value === null) return "Price on request";
  try {
    const formatter = new Intl.NumberFormat("en", { style: "currency", currency });
    const digits = formatter.resolvedOptions().maximumFractionDigits ?? 2;
    return formatter.format(value / 10 ** digits);
  } catch {
    return "Price on request";
  }
}

export default async function PropertyDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const property = await loadProperty(id);
  if (!property) notFound();

  return (
    <main className="property-page">
      <header className="property-header">
        <Link href="/" className="footer-brand">AUREL</Link>
        <nav><Link href="/">Platform</Link><span>/</span><Link href="/properties">Collection</Link><span>/</span><strong>Residence</strong></nav>
        <Link href="/properties" className="property-header-link">Back to collection <span>↗</span></Link>
      </header>
      <section className="detail-intro">
        <div className="eyebrow">ELITE ESTATE · VERIFIED RESIDENCE</div>
        <div className="property-location">{property.city}, {property.country_code}</div>
        <h1>{property.title}</h1>
        <div className="detail-meta"><span>{property.property_type.replaceAll("_", " ")}</span><strong>{formatPrice(property.asking_price_minor, property.currency)}</strong></div>
      </section>
      <div className="detail-layout">
        <article className="detail-description"><div className="eyebrow">THE RESIDENCE</div><p>{property.description}</p><div className="detail-note">Listing information is reviewed before public release. Further documentation is shared through the private office following qualification.</div></article>
        <aside className="detail-enquiry"><div className="eyebrow">PRIVATE ENQUIRY</div><h2>Request further details.</h2><p>Share your interest and a member of the private office will follow up.</p><EnquiryForm propertyId={property.id}/></aside>
      </div>
      <footer className="property-footer"><span>AUREL · PRIVATE PROPERTY</span><span>Verified public inventory only.</span><Link href="/properties">Back to collection</Link></footer>
    </main>
  );
}
