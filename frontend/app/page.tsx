const cards = [
  ["Income", "$0.00", "This month"],
  ["Expenses", "$0.00", "This month"],
  ["Savings", "$0.00", "This month"],
];

export default function Home() {
  return (
    <main className="shell">
      <header className="header">
        <div><p className="eyebrow">PERSONAL FINANCE</p><h1>Your money, clearly.</h1></div>
        <button className="button">Import CSV</button>
      </header>
      <section className="welcome"><p className="eyebrow">MONTHLY OVERVIEW</p><h2>Good morning.</h2><p>Import a bank statement to start understanding your spending.</p></section>
      <section className="cards">{cards.map(([label, value, note]) => <article className="card" key={label}><p>{label}</p><strong>{value}</strong><small>{note}</small></article>)}</section>
      <section className="empty"><div className="icon">＋</div><h2>No transactions yet</h2><p>Upload a CSV statement and we’ll organize your income and expenses into a simple monthly view.</p><button className="button">Upload your first statement</button></section>
    </main>
  );
}
