import Link from "next/link";

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

type SearchParams = {
  country_code?: string;
  city?: string;
  property_type?: string;
};

async function loadProperties(filters: SearchParams): Promise<Property[]> {
  const base = process.env.AUREL_API_URL;
  if (!base) return [];
  const params = new URLSearchParams();
  if (filters.country_code) params.set("country_code", filters.country_code);
  if (filters.city) params.set("city", filters.city);
  if (filters.property_type) params.set("property_type", filters.property_type);
  try {
    const response = await fetch(`${base.replace(/\/$/, "")}/public/properties?${params.toString()}`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
    if (!response.ok) return [];
    const data: unknown = await response.json();
    return Array.isArray(data) ? (data as Property[]) : [];
  } catch {
    return [];
  }
}

function formatPrice(value: number | null, currency: string): string {
  if (value === null) return "Price on request";
  try {
    const formatter = new Intl.NumberFormat("en", { style: "currency", currency });
    const digits = formatter.resolvedOptions().maximumFractionDigits;
    return formatter.format(value / 10 ** digits);
  } catch {
    return "Price on request";
  }
}

export default async function PropertiesPage({ searchParams }: { searchParams: Promise<SearchParams> }) {
  const filters = await searchParams;
  const apiConfigured = Boolean(process.env.AUREL_API_URL);
  const properties = await loadProperties(filters);

  return (
    <main className="property-page">
      <header className="property-header">
        <Link href="/" className="footer-brand">AUREL</Link>
        <nav><Link href="/">Platform</Link><span>/</span><strong>Property collection</strong></nav>
        <Link href="/#services" className="property-header-link">Private office <span>↗</span></Link>
      </header>
      <section className="property-intro">
        <div className="eyebrow">ELITE ESTATE · VERIFIED INVENTORY</div>
        <h1>Find a place<br/><em>worth belonging to.</em></h1>
        <p>Exceptional residences, presented with source-backed information and reviewed before publication.</p>
      </section>
      <form className="property-filters" action="/properties" method="get">
        <label>City or market<input name="city" defaultValue={filters.city ?? ""} placeholder="Search a location"/></label>
        <label>Country code<input name="country_code" defaultValue={filters.country_code ?? ""} maxLength={2} placeholder="e.g. MC"/></label>
        <label>Property type<select name="property_type" defaultValue={filters.property_type ?? ""}>
          <option value="">All types</option>
          <option value="villa">Villa</option><option value="house">House</option><option value="apartment">Apartment</option>
          <option value="penthouse">Penthouse</option><option value="land">Land</option><option value="commercial">Commercial</option>
        </select></label>
        <button type="submit">Search collection <span>↗</span></button>
      </form>
      <section className="property-results">
        <div className="property-results-heading"><div><div className="eyebrow">THE COLLECTION</div><h2>Available residences</h2></div><span>{properties.length} verified {properties.length === 1 ? "property" : "properties"}</span></div>
        {!apiConfigured ? (
          <div className="property-empty"><span>01</span><h3>Inventory connection pending</h3><p>The public collection will appear here once the dedicated AUREL API and verified inventory are connected. No sample or unverified properties are displayed.</p></div>
        ) : properties.length === 0 ? (
          <div className="property-empty"><span>02</span><h3>No verified properties match this search</h3><p>Try another location or contact the private office to register a search brief.</p><Link href="/#services">Contact the private office ↗</Link></div>
        ) : (
          <div className="property-list">{properties.map((property) => (
            <article className="property-card" key={property.id}>
              <div className="property-card-mark">AUREL <span>·</span> VERIFIED</div>
              <div className="property-card-content"><div className="property-location">{property.city}, {property.country_code}</div><h3>{property.title}</h3><p>{property.description}</p><div className="property-card-bottom"><span>{property.property_type.replaceAll("_", " ")}</span><strong>{formatPrice(property.asking_price_minor, property.currency)}</strong></div></div>
              <Link href={`/properties/${property.id}`} className="property-card-link">View residence ↗</Link>
            </article>
          ))}</div>
        )}
      </section>
      <footer className="property-footer"><span>AUREL · PRIVATE PROPERTY</span><span>Every public listing is subject to verification review.</span><Link href="/">Back to platform</Link></footer>
    </main>
  );
}
