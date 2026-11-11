import { spawn } from "node:child_process";
import { mkdirSync, mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

const output = resolve(".preview-redesign");
mkdirSync(output, { recursive: true });
const profile = mkdtempSync(join(tmpdir(), "festa-browser-"));
const browser = spawn(process.env.FESTA_BROWSER || "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", [
  "--headless=new", "--no-first-run", "--no-default-browser-check",
  "--remote-debugging-address=127.0.0.1", "--remote-debugging-port=9229",
  "--user-data-dir=" + profile, "about:blank",
], { windowsHide: true, stdio: "ignore" });
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
let socket;
const pending = new Map();
let serial = 0;
const exceptions = [];
async function until(action, message, timeout = 25000) {
  const end = Date.now() + timeout;
  while (Date.now() < end) {
    try { const result = await action(); if (result) return result; } catch {}
    await sleep(180);
  }
  throw new Error("Tempo excedido: " + message);
}
function send(method, params = {}) {
  return new Promise((resolve, reject) => {
    const id = ++serial;
    pending.set(id, { resolve, reject });
    socket.send(JSON.stringify({ id, method, params }));
  });
}
async function evaluate(expression) {
  const result = await send("Runtime.evaluate", { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text);
  return result.result.value;
}
async function ready(title) {
  await until(() => evaluate("document.querySelector('h1')?.textContent.includes(" + JSON.stringify(title) + ")"), title);
  await sleep(700);
  await until(() => evaluate("!document.querySelector('[data-testid=stException]')"), "sem erros");
}
async function viewport(width, height) {
  await send("Emulation.setDeviceMetricsOverride", { width, height, deviceScaleFactor: 1, mobile: false });
  await sleep(400);
}
async function screenshot(name) {
  await sleep(350);
  const result = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
  writeFileSync(join(output, name + ".png"), Buffer.from(result.data, "base64"));
}
async function navigate(page) {
  await evaluate("Array.from(document.querySelectorAll('[data-testid=stSidebar] [data-testid=stRadio] label')).find(n => n.textContent.includes(" + JSON.stringify(page) + "))?.click()");
  await ready(page);
}
async function scrollTo(selector) {
  await evaluate("document.querySelector(" + JSON.stringify(selector) + ")?.scrollIntoView({behavior:'instant',block:'start'})");
  await sleep(300);
}
const checks = [];
try {
  await until(async () => {
    const response = await fetch("http://127.0.0.1:9229/json/version");
    return response.ok;
  }, "iniciar Chrome");
  const target = await (await fetch("http://127.0.0.1:9229/json/new?about:blank", { method: "PUT" })).json();
  socket = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((resolve, reject) => { socket.onopen = resolve; socket.onerror = reject; });
  socket.onmessage = ({ data }) => {
    const message = JSON.parse(data);
    if (message.id && pending.has(message.id)) {
      const task = pending.get(message.id); pending.delete(message.id);
      message.error ? task.reject(new Error(message.error.message)) : task.resolve(message.result);
    }
    if (message.method === "Runtime.exceptionThrown") exceptions.push(message.params.exceptionDetails.text);
  };
  await send("Runtime.enable");
  await send("Page.enable");
  await viewport(1440, 1000);
  await send("Page.navigate", { url: "http://127.0.0.1:8511" });
  await ready("Uma boa festa");
  checks.push({ name: "Tema e JavaScript", result: await evaluate("({background:getComputedStyle(document.querySelector('.st-key-hero')).backgroundColor, motion:!!window.__festaMotion, metrics:document.querySelectorAll('[data-testid=stMetric]').length})") });
  checks.push({ name: "Ícones carregados", result: await evaluate("document.querySelectorAll('.festa-icon').length > 0 && Array.from(document.querySelectorAll('.festa-icon')).every(n => n.complete && n.naturalWidth > 0)") });
  checks.push({ name: "Menu ativo destacado", result: await evaluate("getComputedStyle(document.querySelector('[data-testid=stRadioOption][data-selected=true]')).backgroundColor === 'rgb(213, 235, 148)'") });
  checks.push({ name: "Receita sem corte", result: await evaluate("Array.from(document.querySelectorAll('[data-testid=stMetricValue]')).every(n=>n.scrollWidth<=n.clientWidth+1)") });
  await screenshot("01-painel-desktop");
  await scrollTo(".st-key-panel-planning");
  await screenshot("02-planejamento-desktop");
  await navigate("Alimentos");
  await screenshot("03-alimentos-desktop");
  checks.push({ name: "Ações por registro", result: await evaluate("document.querySelectorAll('.festa-row-action').length") });
  await evaluate("document.querySelector('.festa-row-action')?.click()");
  await ready("Alimentos");
  checks.push({ name: "Editar pela tabela", result: await evaluate("Array.from(document.querySelectorAll('input')).some(input => input.value === 'Bolo de chocolate')") });
  await scrollTo(".st-key-editor-alimentos");
  await screenshot("04-formulario-desktop");
  await evaluate("document.querySelector('.festa-row-delete')?.click()");
  await ready("Alimentos");
  checks.push({ name: "Confirmação de exclusão", result: await evaluate("!!document.querySelector('[data-testid=stExpander] details[open]') && Array.from(document.querySelectorAll('input[type=checkbox]')).some(n => !n.checked)") });
  for (const page of ["Insumos", "Composições", "Doadores", "Doações", "Participantes", "Tarefas", "Escalas de trabalho"]) {
    await navigate(page);
    checks.push({ name: "Página: " + page, result: await evaluate("!document.querySelector('[data-testid=stException]') && !!document.querySelector('.festa-table')") });
  }
  await navigate("Doações");
  await screenshot("05-doacoes-desktop");
  await viewport(834, 1112);
  await screenshot("06-doacoes-tablet");
  checks.push({ name: "Tablet sem transbordamento", result: await evaluate("document.documentElement.scrollWidth <= innerWidth") });
  await viewport(390, 844);
  await evaluate("document.querySelector('[data-testid=stSidebarCollapseButton] button')?.click()");
  await sleep(350);
  await scrollTo(".st-key-panel-doacoes");
  await screenshot("07-doacoes-mobile");
  checks.push({ name: "Tabela mobile em cartões", result: await evaluate("getComputedStyle(document.querySelector('.festa-table tbody tr')).display === 'grid'") });
  checks.push({ name: "Celular sem transbordamento", result: await evaluate("document.documentElement.scrollWidth <= innerWidth") });
  await scrollTo(".st-key-editor-doacoes");
  await screenshot("08-formulario-mobile");
  await send("Emulation.setEmulatedMedia", { features: [{ name: "prefers-reduced-motion", value: "reduce" }] });
  await sleep(350);
  checks.push({ name: "Movimento reduzido", result: await evaluate("({matches:matchMedia('(prefers-reduced-motion:reduce)').matches, animation:getComputedStyle(document.querySelector('.st-key-page-heading')).animationName, hidden:Array.from(document.querySelectorAll('.festa-reveal-ready')).some(n=>getComputedStyle(n).opacity==='0')})") });
  await send("Page.navigate", { url: "http://127.0.0.1:8511/?section=painel" });
  await ready("Uma boa festa");
  await screenshot("09-painel-mobile");
  await viewport(834, 1112);
  await screenshot("10-painel-tablet");
  checks.push({ name: "Erros JavaScript", result: exceptions });
  writeFileSync(join(output, "review.json"), JSON.stringify(checks, null, 2));
  console.log(JSON.stringify({ screenshots: output, checks }, null, 2));
  if (checks.some(check => check.result === false) || exceptions.length) {
    process.exitCode = 1;
  }
} finally {
  if (socket?.readyState === WebSocket.OPEN) {
    try { await send("Browser.close"); } catch {}
    socket.close();
  }
  browser.kill();
}
