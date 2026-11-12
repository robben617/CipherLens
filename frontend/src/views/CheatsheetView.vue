<template>
  <main class="cs">
    <header class="cs__head">
      <div class="cs__intro">
        <p class="cs__eyebrow">速查卡 · AES-128</p>
        <h1 class="cs__title">手算时摊在桌上的一页</h1>
        <p class="cs__lede">
          四步怎么走、S 盒在哪查、轮常数是几、40 步怎么编号。打印成 A4 双面：
          正面四步与 S 盒，背面轮常数与 40 步表，贴在桌边手算时不用来回切页面。
        </p>
      </div>

      <div class="cs__tools no-print">
        <button type="button" class="cs__btn cs__btn--go" data-action="print" @click="printPage">
          打印这一页
        </button>
        <RouterLink class="cs__btn" to="/workbench">回工作台</RouterLink>
      </div>
    </header>

    <!-- ① 四步 -->
    <section class="cs__sec" aria-labelledby="cs-four">
      <h2 id="cs-four" class="cs__h2"><span class="cs__h2no">一</span>一轮就是这四步，重复十轮</h2>

      <div class="cs__four">
        <article v-for="s in FOUR" :key="s.en" class="cs__step" :class="`is-${s.tone}`">
          <header class="cs__step-head">
            <span class="cs__step-no" aria-hidden="true">{{ s.no }}</span>
            <div>
              <h3 class="cs__step-name">{{ s.name }}</h3>
              <code class="cs__step-en">{{ s.en }}</code>
            </div>
          </header>

          <div class="cs__mini" aria-hidden="true">
            <span
              v-for="i in 16"
              :key="i"
              class="cs__mini-cell"
              :style="cellStyle(i)"
            />
          </div>

          <p class="cs__formula">{{ s.formula }}</p>
          <p class="cs__note">{{ s.note }}</p>
        </article>
      </div>

      <p class="cs__tail">
        <b>第 10 轮没有列混合</b>——不是省略，是设计如此：末轮少一步，解密时才能对称地反过来走。
        状态矩阵按<b>列</b>存放，第 1 列是最前面 4 个字节。
      </p>
    </section>

    <!-- ② S 盒 -->
    <section class="cs__sec" aria-labelledby="cs-sbox">
      <h2 id="cs-sbox" class="cs__h2"><span class="cs__h2no">二</span>S 盒（正向，字节代换就查这张）</h2>
      <p class="cs__sub">
        行 = 输入的高 4 位，列 = 输入的低 4 位。
        <span class="cs__eg">查 0x3F：第 3 行第 F 列 → <b>0x75</b></span>
      </p>

      <table class="cs__sbox" data-sbox-table>
        <caption class="sr-only">AES 正向 S 盒，16 行 16 列</caption>
        <thead>
          <tr>
            <th scope="col" class="cs__sbox-corner"><span class="sr-only">高/低</span></th>
            <th v-for="c in 16" :key="c" scope="col">{{ hex(c - 1) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in 16" :key="r">
            <th scope="row">{{ hex(r - 1) }}</th>
            <td v-for="c in 16" :key="c">{{ hex(values[(r - 1) * 16 + (c - 1)]!) }}</td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- ③ 轮常数与密钥扩展 -->
    <section class="cs__sec cs__sec--break" aria-labelledby="cs-rcon">
      <h2 id="cs-rcon" class="cs__h2"><span class="cs__h2no">三</span>轮常数与密钥怎么长出来</h2>

      <div class="cs__split">
        <div>
          <p class="cs__sub">Rcon[1] – Rcon[10]（GF(2⁸) 上每次乘 2，溢出就异或 0x1b）</p>
          <table class="cs__rcon" data-rcon-table>
            <thead>
              <tr>
                <th scope="col">i</th>
                <th v-for="i in 10" :key="i" scope="col">{{ i }}</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <th scope="row">Rcon</th>
                <td v-for="(v, i) in RCON" :key="i">{{ hex(v) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <ol class="cs__g">
          <li><b>RotWord</b>：把 4 字节循环左移一格（<code>a0 a1 a2 a3</code> → <code>a1 a2 a3 a0</code>）</li>
          <li><b>SubWord</b>：这 4 个字节各查一次 S 盒</li>
          <li><b>异或 Rcon</b>：只异或第 1 个字节，后面 3 个不变</li>
        </ol>
      </div>

      <p class="cs__tail">
        128 位密钥共 4 个字（w0–w3），要长到 44 个字：<code>w[i] = w[i−4] ⊕ g(w[i−1])</code>，
        <b>i 不是 4 的倍数时不走 g</b>，直接 <code>w[i] = w[i−4] ⊕ w[i−1]</code>。
      </p>
    </section>

    <!-- ④ 40 步对照表 -->
    <section class="cs__sec" aria-labelledby="cs-steps">
      <h2 id="cs-steps" class="cs__h2"><span class="cs__h2no">四</span>40 步怎么编号</h2>
      <p class="cs__sub">
        第 1 步是加密前的轮密钥加，之后每轮 4 步，最后一轮只有 3 步。
        <span class="cs__eg">工作台右下角的「第 N 步」就是这张表的 N</span>
      </p>

      <div class="cs__tables">
        <table class="cs__steps" data-step-table>
          <thead>
            <tr>
              <th scope="col">步</th>
              <th scope="col">轮</th>
              <th scope="col">变换</th>
              <th scope="col">这一步做了什么</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in STEP_TABLE.slice(0, 20)" :key="s.no" :class="{ 'is-last': s.round === 10 }">
              <td class="cs__no">{{ s.no }}</td>
              <td class="cs__round">{{ s.round }}</td>
              <td>{{ s.label }}</td>
              <td class="cs__what">{{ s.what }}</td>
            </tr>
          </tbody>
        </table>

        <table class="cs__steps" aria-label="第 21 到 40 步">
          <thead>
            <tr>
              <th scope="col">步</th>
              <th scope="col">轮</th>
              <th scope="col">变换</th>
              <th scope="col">这一步做了什么</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in STEP_TABLE.slice(20)" :key="s.no" :class="{ 'is-last': s.round === 10 }">
              <td class="cs__no">{{ s.no }}</td>
              <td class="cs__round">{{ s.round }}</td>
              <td>{{ s.label }}</td>
              <td class="cs__what">{{ s.what }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <footer class="cs__foot">
      <span>全部数值来自 FIPS-197 附录 B / C，与应用内引擎同源</span>
      <span>CipherLens · 速查卡 v1</span>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import type { CSSProperties } from 'vue'
import { RCON } from '../engine/aes'
import { SBOX } from '../engine/sbox'
import { STEP_TABLE } from '../data/step-table'

/** S 盒是 Uint8Array，模板里按下标取；照抄一份引用，避免模板里出现类型断言。 */
const values: readonly number[] = Array.from(SBOX)

const FOUR = [
  {
    no: '01',
    name: '字节代换',
    en: 'SubBytes',
    tone: 'sub',
    formula: "b′ = S[b]",
    note: '16 个格子各自查表，互不影响。这是全流程里唯一「非线性」的一步。',
  },
  {
    no: '02',
    name: '行移位',
    en: 'ShiftRows',
    tone: 'shift',
    formula: '行 0 / 1 / 2 / 3 左移 0 / 1 / 2 / 3 格',
    note: '位移量由行号决定，与字节值无关。一列里的 4 个字节因此被拆到 4 个不同列。',
  },
  {
    no: '03',
    name: '列混合',
    en: 'MixColumns',
    tone: 'mix',
    formula: '[02 03 01 01] × 列',
    note: '每列 4 个字节乘同一个固定矩阵。顺序不变，值全变——一个字节动了整列跟着动。',
  },
  {
    no: '04',
    name: '轮密钥加',
    en: 'AddRoundKey',
    tone: 'ark',
    formula: 's′ = s ⊕ k',
    note: '异或，不是算术加法，没有进位。同一把轮密钥再用一次就还原。',
  },
] as const

function hex(value: number): string {
  return value.toString(16).toUpperCase().padStart(2, '0')
}

/** 4×4 示意格里每格需要行号：行移位按行错位，行号只能从模板传下去。 */
function cellStyle(index: number): CSSProperties {
  return { '--r': String(Math.floor((index - 1) / 4)) } as CSSProperties
}

function printPage(): void {
  window.print()
}
</script>

<style scoped>
.cs {
  --cs-w: 960px;
  max-width: var(--cs-w);
  margin: 0 auto;
  padding: var(--sp-8) var(--sp-6) var(--sp-16);
}

/* ============ 页头 ============ */
.cs__head {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-4);
  align-items: flex-end;
  justify-content: space-between;
  padding-bottom: var(--sp-4);
  border-bottom: var(--rule-region-w) solid var(--line-default);
}

.cs__intro {
  min-width: 0;
}

.cs__eyebrow {
  margin: 0 0 var(--sp-2);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.cs__title {
  margin: 0 0 var(--sp-2);
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  font-weight: 500;
  line-height: var(--lh-tight);
  color: var(--ink-1);
}

.cs__lede {
  margin: 0;
  max-width: 34rem;
  font-size: var(--fs-body);
  line-height: 1.7;
  color: var(--ink-2);
}

.cs__tools {
  display: flex;
  gap: var(--sp-2);
}

.cs__btn {
  display: inline-flex;
  align-items: center;
  height: 36px;
  padding: 0 var(--sp-3);
  border: var(--rule-region-w) solid var(--line-default);
  border-radius: var(--r-control);
  background: transparent;
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  color: var(--ink-2);
  text-decoration: none;
  cursor: pointer;
  white-space: nowrap;
}

.cs__btn:hover {
  border-color: var(--accent);
  color: var(--accent-strong);
}

.cs__btn--go {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--paper-0);
}

.cs__btn--go:hover {
  background: var(--accent-strong);
  border-color: var(--accent-strong);
  color: var(--paper-0);
}

/* ============ 通用小节 ============ */
.cs__sec {
  margin-top: var(--sp-8);
}

.cs__h2 {
  display: flex;
  align-items: baseline;
  gap: var(--sp-2);
  margin: 0 0 var(--sp-3);
  font-family: var(--font-display);
  font-size: var(--fs-h2);
  font-weight: 500;
  color: var(--ink-1);
}

.cs__h2no {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 22px;
  height: 22px;
  border: var(--rule-region-w) solid var(--line-strong);
  border-radius: 50%;
  font-family: var(--font-ui);
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

.cs__sub {
  margin: 0 0 var(--sp-3);
  font-size: var(--fs-ui);
  line-height: 1.7;
  color: var(--ink-2);
}

.cs__eg {
  color: var(--ink-3);
}

.cs__tail {
  margin: var(--sp-3) 0 0;
  padding: var(--sp-3);
  border-left: 2px solid var(--line-default);
  font-size: var(--fs-label);
  line-height: 1.75;
  color: var(--ink-2);
}

.cs__tail code,
.cs__g code {
  font-family: var(--font-mono);
  font-size: 0.95em;
  color: var(--ink-1);
}

/* ============ ① 四步 ============ */
.cs__four {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sp-3);
}

.cs__step {
  display: flex;
  flex-direction: column;
  gap: var(--sp-2);
  padding: var(--sp-3);
  border: var(--rule-region-w) solid var(--line-hairline);
  border-top: 3px solid var(--tone-ink);
  border-radius: var(--r-cell);
  background: var(--paper-0);
}

.cs__step.is-sub {
  --tone-tint: var(--step-sub-tint);
  --tone-ink: var(--step-sub-ink);
}

.cs__step.is-shift {
  --tone-tint: var(--step-shift-tint);
  --tone-ink: var(--step-shift-ink);
}

.cs__step.is-mix {
  --tone-tint: var(--step-mix-tint);
  --tone-ink: var(--step-mix-ink);
}

.cs__step.is-ark {
  --tone-tint: var(--step-ark-tint);
  --tone-ink: var(--step-ark-ink);
}

.cs__step-head {
  display: flex;
  align-items: center;
  gap: var(--sp-2);
}

.cs__step-no {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--tone-ink);
}

.cs__step-name {
  margin: 0;
  font-size: var(--fs-h3);
  font-weight: 500;
  color: var(--ink-1);
}

.cs__step-en {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  color: var(--ink-4);
}

/* 4×4 示意：只表达「哪一步在动哪一批格子」 */
.cs__mini {
  display: grid;
  grid-template-columns: repeat(4, 11px);
  gap: 3px;
  margin: var(--sp-1) 0;
}

.cs__mini-cell {
  width: 11px;
  height: 11px;
  border: 1px solid var(--line-default);
  border-radius: 2px;
  background: var(--paper-0);
}

.is-sub .cs__mini-cell {
  border-color: var(--tone-ink);
  background: var(--tone-tint);
}

/* 三行各自右移，视觉上错开，不动布局（格子本身仍在栅格内） */
.is-shift .cs__mini-cell {
  border-color: var(--tone-ink);
  background: var(--tone-tint);
  transform: translateX(calc(var(--r) * 2px));
}

.is-mix .cs__mini-cell {
  border-color: var(--tone-ink);
  background: var(--tone-tint);
}

/* 列混合按列着色：列间留出更宽的缝，读成「一整列一起算」 */
.is-mix .cs__mini {
  column-gap: 5px;
}

.is-ark .cs__mini-cell:nth-child(even) {
  border-color: var(--tone-ink);
  background: var(--tone-tint);
}

.cs__formula {
  margin: 0;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  line-height: 1.5;
  color: var(--tone-ink);
}

.cs__note {
  margin: 0;
  font-size: var(--fs-label);
  line-height: 1.65;
  color: var(--ink-2);
}

/* ============ ② S 盒 ============ */
.cs__sbox {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--fs-sbox);
  line-height: 1;
  table-layout: fixed;
}

.cs__sbox th,
.cs__sbox td {
  padding: 4px 0;
  text-align: center;
  border: 1px solid var(--line-hairline);
  color: var(--ink-2);
}

.cs__sbox thead th,
.cs__sbox tbody th {
  background: var(--paper-1);
  color: var(--ink-3);
  font-weight: 400;
}

.cs__sbox tbody td {
  color: var(--ink-1);
}

.cs__sbox-corner {
  width: 34px;
}

/* ============ ③ 轮常数 ============ */
.cs__split {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  gap: var(--sp-6);
  align-items: start;
}

.cs__rcon {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--fs-label);
  table-layout: fixed;
}

.cs__rcon th,
.cs__rcon td {
  padding: 5px 0;
  text-align: center;
  border: 1px solid var(--line-hairline);
  color: var(--ink-1);
}

.cs__rcon thead th,
.cs__rcon tbody th {
  background: var(--paper-1);
  color: var(--ink-3);
  font-weight: 400;
}

.cs__g {
  margin: 0;
  padding-left: 1.25em;
  font-size: var(--fs-label);
  line-height: 1.8;
  color: var(--ink-2);
}

/* ============ ④ 40 步 ============ */
.cs__tables {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--sp-4);
}

.cs__steps {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--fs-label);
  line-height: 1.35;
  table-layout: fixed;
}

.cs__steps th,
.cs__steps td {
  padding: 4px 6px;
  text-align: left;
  border-bottom: 1px solid var(--line-hairline);
  color: var(--ink-2);
}

.cs__steps thead th {
  border-bottom: var(--rule-region-w) solid var(--line-strong);
  font-weight: 500;
  color: var(--ink-3);
  font-size: var(--fs-micro);
}

.cs__steps th:nth-child(1) {
  width: 2.4em;
}

.cs__steps th:nth-child(2) {
  width: 2.2em;
}

.cs__steps th:nth-child(3) {
  width: 6.2em;
}

.cs__steps tbody tr.is-last td {
  background: var(--step-ark-tint);
}

.cs__no,
.cs__round {
  font-family: var(--font-mono);
  color: var(--ink-3);
}

.cs__what {
  font-size: var(--fs-micro);
  color: var(--ink-3);
}

/* ============ 页脚 ============ */
.cs__foot {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-2) var(--sp-4);
  justify-content: space-between;
  margin-top: var(--sp-8);
  padding-top: var(--sp-3);
  border-top: var(--rule-region-w) solid var(--line-hairline);
  font-size: var(--fs-micro);
  color: var(--ink-4);
}

/* ============ 窄屏 ============ */
@media (max-width: 900px) {
  .cs {
    padding: var(--sp-6) var(--sp-4) var(--sp-12);
  }

  .cs__four {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .cs__split {
    grid-template-columns: 1fr;
    gap: var(--sp-4);
  }

  .cs__tables {
    grid-template-columns: 1fr;
  }

  .cs__sbox {
    font-size: var(--fs-micro);
  }
}

@media (max-width: 560px) {
  .cs__four {
    grid-template-columns: 1fr;
  }

  .cs__sbox th,
  .cs__sbox td {
    padding: 3px 0;
    font-size: 0.625rem;
  }

  .cs__what {
    display: none; /* 手机上先保住「步 / 轮 / 变换」三列 */
  }

  .cs__steps th:nth-child(4) {
    display: none;
  }
}

/* ============ 打印 ============ */
@media print {
  /* A4 宽 210mm ≈ 794px，会命中上面 900px 的窄屏断点，所以这里必须把栅格改回来，
     否则打印出来是手机版：四步变两列、40 步表上下堆两页。 */
  .cs__four {
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 3mm;
  }

  .cs__tables {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 4mm;
  }

  .cs__split {
    grid-template-columns: minmax(0, 1.15fr) minmax(0, 1fr);
  }

  .cs {
    max-width: none;
    padding: 0;
  }

  .no-print {
    display: none !important;
  }

  .cs__sec {
    margin-top: 8mm;
    break-inside: avoid;
  }

  /* 正面：四步 + S 盒；背面：轮常数 + 40 步。
     实测整页内容 1693px，A4 一页只有约 1033px，硬压只能靠 6pt 字号——
     不如在「二 / 三」之间强制分页，双面打印各占一面，表格不会被切断。 */
  .cs__sec--break {
    break-before: page;
  }

  .cs__sbox th,
  .cs__sbox td {
    padding: 2px 0;
    font-size: 7pt;
  }

  .cs__steps th,
  .cs__steps td {
    padding: 1.6px 4px;
    font-size: 7.5pt;
  }

  .cs__note,
  .cs__tail,
  .cs__sub {
    font-size: 8pt;
  }

  .cs__foot {
    margin-top: 6mm;
  }
}
</style>
