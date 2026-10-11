import Link from 'next/link';

export default function ContactPage() {
  const email = process.env.NEXT_PUBLIC_CONTACT_EMAIL?.trim() || 'mangobyte.kew@gmail.com';
  return <section className="contact-page">
    <div className="page-heading"><div><span className="eyebrow">Get in touch</span><h1>Contact us</h1><p>Have a question or something to share? We'd like to hear from you.</p></div></div>
    <div className="panel contact-panel"><h2>Talk to the Kew team</h2>
      {email ? <><p>Send us an email and let us know how we can help.</p><a className="button primary" href={`mailto:${email}`}>{email}</a></> : <p>Our contact details will be available here soon.</p>}
    </div>
    <Link href="/" className="contact-link">Back to Overview</Link>
  </section>;
}
