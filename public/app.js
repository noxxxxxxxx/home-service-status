const overall = document.getElementById("overall");
const checkedAt = document.getElementById("checked-at");
const list = document.getElementById("services");

function timeLabel(value) {
  return new Intl.DateTimeFormat("zh-CN", { dateStyle: "medium", timeStyle: "short", timeZone: "Asia/Shanghai" }).format(new Date(value)) + "（北京时间）";
}

function timeline(history, id) {
  const recent = history.slice(-96);
  const missing = Math.max(0, 96 - recent.length);
  const slots = [...Array(missing).fill(null), ...recent.map(row => row[id])];
  const box = document.createElement("div");
  box.className = "timeline";
  box.setAttribute("aria-label", `${id} 最近 24 小时监测记录`);
  for (const value of slots) {
    const bar = document.createElement("span");
    bar.className = "bar " + (value === null ? "empty" : value ? "" : "down");
    box.append(bar);
  }
  return box;
}

function renderService(service, history, stale) {
  const card = document.createElement("article");
  card.className = `service ${stale ? "unknown" : service.up ? "up" : "down"}`;
  const top = document.createElement("div");
  top.className = "service-top";
  const name = document.createElement("div");
  name.className = "service-name";
  const dot = document.createElement("span");
  dot.className = "dot";
  name.append(dot, document.createTextNode(service.name));
  const link = document.createElement("a");
  link.href = service.url;
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.textContent = "访问服务 ↗";
  top.append(name, link);
  const meta = document.createElement("div");
  meta.className = "service-meta";
  const observations = history.slice(-96).filter(row => typeof row[service.id] === "boolean");
  const uptime = observations.length ? Math.round(observations.filter(row => row[service.id]).length / observations.length * 100) + "%" : "—";
  const failed = Object.entries(service.checks).filter(([, result]) => !result.ok).map(([key, result]) => `${key === "page" ? "页面" : "JS"}：${result.detail}`);
  const detail = stale ? "监测延迟" : service.up ? "访问正常" : failed.join(" · ");
  meta.append(document.createTextNode(detail + " · 最近记录可用率 "));
  const strong = document.createElement("strong");
  strong.textContent = uptime;
  meta.append(strong);
  card.append(top, meta, timeline(history, service.id));
  const caption = document.createElement("div");
  caption.className = "timeline-caption";
  caption.innerHTML = "<span>24 小时前</span><span>现在</span>";
  card.append(caption);
  return card;
}

async function refresh() {
  try {
    const [statusResponse, historyResponse] = await Promise.all([
      fetch("./status.json", { cache: "no-store" }),
      fetch("./history.json", { cache: "no-store" }),
    ]);
    if (!statusResponse.ok || !historyResponse.ok) throw new Error("status unavailable");
    const status = await statusResponse.json();
    const history = await historyResponse.json();
    const stale = Date.now() - new Date(status.checkedAt).getTime() > 45 * 60 * 1000;
    const up = status.services.filter(service => service.up).length;
    overall.className = stale ? "warn" : up === status.services.length ? "good" : "bad";
    overall.textContent = stale ? "监测延迟，状态待确认" : up === status.services.length ? "所有服务正常" : `${up} / ${status.services.length} 项服务正常`;
    checkedAt.dateTime = status.checkedAt;
    checkedAt.textContent = timeLabel(status.checkedAt);
    list.replaceChildren(...status.services.map(service => renderService(service, history, stale)));
  } catch {
    overall.className = "warn";
    overall.textContent = "暂时无法读取监测结果";
    checkedAt.textContent = "—";
    list.replaceChildren();
  }
}

refresh();
setInterval(refresh, 60_000);
