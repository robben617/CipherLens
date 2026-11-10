<template>
  <main class="home">
    <!-- ① Hero -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero__text">
        <p class="hero__eyebrow">AES-128 · 逐步可视化</p>

        <h1 id="hero-title" class="hero__title">把 AES 拆开给你看。</h1>

        <p class="hero__lede">
          左边输入 16 个字节，右边看着它们被一步步打乱，最后变成谁也认不出的密文。
          每一步都会告诉你：它在做什么、为什么这么做、哪些格子被改了。
        </p>

        <p class="hero__lede hero__lede--soft">
          你不需要先学完数学——遇到那一步，再讲那一步的数学。
        </p>

        <div class="hero__cta">
          <RouterLink class="btn btn--primary" to="/workbench">看一次真实的加密</RouterLink>
          <RouterLink class="btn btn--ghost" :to="{ path: '/workbench', query: { tour: '1' } }">
            我完全不懂，带我走一遍
          </RouterLink>
        </div>
      </div>

      <div class="hero__demo">
        <HeroMatrix />
      </div>
    </section>

    <!-- ② 为什么大多数教程看不下去 -->
    <section class="sec" aria-labelledby="why-title">
      <h2 id="why-title" class="sec__title">为什么大多数 AES 教程看不下去</h2>
      <div class="why-grid">
        <WhyCard
          icon="box"
          title="加密像一个黑箱"
          body="进去一段数据，出来一段密文，中间什么都没看见。看完还是不知道为什么。"
        />
        <WhyCard
          icon="text"
          title="术语先于理解"
          body="上来就是状态矩阵、S 盒、有限域，第一页就劝退，还不知道这些东西是干什么用的。"
        />
        <WhyCard
          icon="pin"
          title="错了不知道错在哪"
          body="手算填错一个字节，只知道「错」，不知道是第几步错的，也不知道该回看哪一格。"
        />
      </div>
    </section>

    <!-- ③ 前置三件事 -->
    <section class="sec sec--tight" aria-labelledby="need-title">
      <h2 id="need-title" class="sec__title">其实只需要先知道三件事</h2>

      <ol class="needs">
        <li class="needs__item">
          <span class="needs__no" aria-hidden="true">01</span>
          <p class="needs__text">
            一个字节 = 8 位 = 两个十六进制数字。<span class="needs__eg">比如 0x3F 就是 0011 1111。</span>
          </p>
        </li>
        <li class="needs__item">
          <span class="needs__no" aria-hidden="true">02</span>
          <p class="needs__text">
            异或：两位相同得 0，不同得 1。<span class="needs__eg">它最大的好处是「再算一次就还原」。</span>
          </p>
        </li>
        <li class="needs__item">
          <span class="needs__no" aria-hidden="true">03</span>
          <p class="needs__text">
            矩阵按列读：第 1 列是最前面 4 个字节，<span class="needs__eg">不是第一行。</span>
          </p>
        </li>
      </ol>

      <p class="sec__note">其余的（有限域、仿射变换、矩阵乘法）遇到那一步再讲，不用提前学。</p>
    </section>

    <!-- ④ 四步 -->
    <section class="sec" aria-labelledby="steps-title">
      <h2 id="steps-title" class="sec__title">一轮就是这四步，重复十轮</h2>
      <p class="sec__note sec__note--lead">
        最后一轮少一步列混合——这不是省略，是设计如此。
      </p>

      <div class="step-grid">
        <StepCard
          v-for="s in STEPS"
          :key="s.en"
          :no="s.no"
          :name="s.name"
          :en="s.en"
          :body="s.body"
          :tone="s.tone"
          :step="s.step"
        />
      </div>
    </section>

    <!-- ⑤ 三种用法 -->
    <section class="sec sec--tight" aria-labelledby="use-title">
      <h2 id="use-title" class="sec__title">三种用法</h2>
      <ul class="uses">
        <li v-for="u in USES" :key="u.no" class="uses__row">
          <span class="uses__no" aria-hidden="true">{{ u.no }}</span>
          <div class="uses__body">
            <h3 class="uses__name">{{ u.name }}</h3>
            <p class="uses__text">{{ u.text }}</p>
          </div>
          <RouterLink class="uses__link" :to="u.to">{{ u.cta }} →</RouterLink>
        </li>
      </ul>
    </section>

    <!-- ⑥ 页脚 -->
    <footer class="foot">
      <span>FastAPI · Vue 3 · SQLite</span>
      <span>已通过 FIPS-197 附录 C 向量校验</span>
      <span class="foot__ver">v0.1</span>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import HeroMatrix from '../components/home/HeroMatrix.vue'
import StepCard from '../components/home/StepCard.vue'
import WhyCard from '../components/home/WhyCard.vue'

const STEPS = [
  {
    no: '01',
    name: '字节代换',
    en: 'SubBytes',
    body: '每个字节去 S 盒里查一下，换成表里对应的那个值。不是随便换——表是固定的，谁算都是同一个结果。',
    tone: 'sub',
    step: 1,
  },
  {
    no: '02',
    name: '行移位',
    en: 'ShiftRows',
    body: '第 1 行不动，第 2 行左移 1 格，第 3 行左移 2 格，第 4 行左移 3 格。位移量由行号决定。',
    tone: 'shift',
    step: 2,
  },
  {
    no: '03',
    name: '列混合',
    en: 'MixColumns',
    body: '每列 4 个字节乘一个固定矩阵。顺序完全不变，值全变了——一个字节动了，整列都跟着变。',
    tone: 'mix',
    step: 3,
  },
  {
    no: '04',
    name: '轮密钥加',
    en: 'AddRoundKey',
    body: '16 个字节和本轮密钥按位异或。注意是异或，不是算术加法——没有进位。',
    tone: 'ark',
    step: 4,
  },
] as const

const USES = [
  {
    no: '01',
    name: '看',
    text: '在工作台输入自己的明文和密钥，一步步走完 41 步，每一步都有解说和「哪些格子被改了」。',
    cta: '进工作台',
    to: '/workbench',
  },
  {
    no: '02',
    name: '练',
    text: '做判分题。答错会告诉你第一个错的字节在第几步、由哪些字节一起算出来。',
    cta: '去做题',
    to: '/practice',
  },
  {
    no: '03',
    name: '记',
    text: '每次练习都会留下记录，可以回看自己总卡在哪一步、哪一类错误反复出现。',
    cta: '看记录',
    to: '/records',
  },
] as const
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--sp-16) var(--sp-6) var(--sp-8);
}

/* ============ ① Hero ============ */
.hero {
  display: grid;
  /* 第二列取 auto：矩阵按自身宽度贴右，不撑在 5/12 的列里居中留空 */
  grid-template-columns: minmax(0, 1fr) auto;
  gap: var(--sp-12);
  align-items: center;
}

.hero__text {
  min-width: 0;
}

.hero__eyebrow {
  margin: 0 0 var(--sp-3);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-3);
}

.hero__title {
  margin: 0 0 var(--sp-4);
  max-width: var(--measure-hero);
  font-family: var(--font-display);
  font-size: clamp(2.25rem, 1.4rem + 2.4vw, 3.5rem);
  font-weight: 500;
  line-height: var(--lh-tight);
  letter-spacing: 0.01em;
  color: var(--ink-1);
  /* 窄屏折行时让两行等长，避免「看。」单独一行 */
  text-wrap: balance;
}

.hero__lede {
  margin: 0 0 var(--sp-3);
  /* 设计稿写 34ch，但 ch 按西文「0」宽估算，中文下只排得下约 17 字，折行过碎。
     中文语境换算为 32rem（约 30 字一行）。 */
  max-width: 32rem;
  font-size: 1rem;
  line-height: 1.75;
  color: var(--ink-2);
}

.hero__lede--soft {
  color: var(--ink-3);
}

.hero__cta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-3);
  margin-top: var(--sp-6);
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  padding: 0 var(--sp-4);
  border-radius: var(--r-control);
  font-family: var(--font-ui);
  font-size: var(--fs-ui);
  text-decoration: none;
  transition: background var(--d-2) var(--e-out-quart), border-color var(--d-2) var(--e-out-quart);
}

.btn--primary {
  border: var(--rule-region-w) solid var(--accent);
  background: var(--accent);
  color: var(--paper-0);
}

.btn--primary:hover {
  border-color: var(--accent-strong);
  background: var(--accent-strong);
}

.btn--ghost {
  border: var(--rule-region-w) solid var(--line-strong);
  background: transparent;
  color: var(--ink-1);
}

.btn--ghost:hover {
  border-color: var(--ink-2);
}

.hero__demo {
  display: flex;
  justify-content: flex-end;
  min-width: 0;
}

/* ============ 段落通用 ============ */
.sec {
  margin-top: var(--sp-16);
}

.sec--tight {
  margin-top: var(--sp-12);
}

.sec__title {
  margin: 0 0 var(--sp-4);
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--ink-1);
}

.sec__note {
  margin: var(--sp-3) 0 0;
  max-width: var(--measure);
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-3);
}

.sec__note--lead {
  margin: calc(var(--sp-2) * -1) 0 var(--sp-4);
}

/* ============ ② 为什么难 ============ */
.why-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--sp-3);
}

/* ============ ③ 三件事 ============ */
.needs {
  display: grid;
  gap: var(--sp-2);
  margin: 0;
  padding: 0;
  list-style: none;
  max-width: var(--measure);
}

.needs__item {
  display: flex;
  align-items: baseline;
  gap: var(--sp-3);
  padding: var(--sp-3) 0;
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.needs__item:last-child {
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.needs__no {
  flex: none;
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-4);
}

.needs__text {
  margin: 0;
  font-size: var(--fs-body);
  line-height: var(--lh-body);
  color: var(--ink-1);
}

.needs__eg {
  color: var(--ink-2);
}

/* ============ ④ 四步 ============ */
.step-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--sp-3);
}

/* ============ ⑤ 三种用法 ============ */
.uses {
  margin: 0;
  padding: 0;
  list-style: none;
}

.uses__row {
  display: grid;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  align-items: baseline;
  gap: var(--sp-3);
  padding: var(--sp-3) 0;
  border-top: var(--rule-region-w) solid var(--line-hairline);
}

.uses__row:last-child {
  border-bottom: var(--rule-region-w) solid var(--line-hairline);
}

.uses__no {
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-label);
  color: var(--ink-4);
}

.uses__name {
  margin: 0 0 2px;
  font-family: var(--font-display);
  font-size: var(--fs-h3);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--ink-1);
}

.uses__text {
  margin: 0;
  max-width: 62ch;
  font-size: var(--fs-ui);
  line-height: var(--lh-body);
  color: var(--ink-2);
}

.uses__link {
  font-size: var(--fs-ui);
  color: var(--accent-strong);
  text-decoration: none;
  white-space: nowrap;
  padding-block: var(--sp-1);
  border-bottom: var(--rule-region-w) solid transparent;
}

.uses__link:hover {
  border-bottom-color: currentColor;
}

/* ============ ⑥ 页脚 ============ */
.foot {
  display: flex;
  flex-wrap: wrap;
  gap: var(--sp-4);
  margin-top: var(--sp-12);
  padding-top: var(--sp-4);
  border-top: var(--rule-region-w) solid var(--line-hairline);
  font-family: var(--font-mono);
  font-size: var(--fs-micro);
  letter-spacing: var(--ls-hex-long);
  color: var(--ink-3);
}

.foot__ver {
  margin-left: auto;
  color: var(--ink-4);
}

/* ============ 响应式 ============ */
@media (max-width: 1100px) {
  .step-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 900px) {
  .hero {
    grid-template-columns: minmax(0, 1fr);
    gap: var(--sp-8);
  }

  .hero__lede {
    max-width: none;
  }

  .hero__demo {
    justify-content: flex-start;
  }

  .why-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .uses__row {
    grid-template-columns: 28px minmax(0, 1fr);
    row-gap: var(--sp-2);
  }

  .uses__link {
    grid-column: 2;
  }
}

@media (max-width: 700px) {
  .home {
    padding-top: var(--sp-8);
  }

  .step-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .btn {
    width: 100%;
  }
}
</style>
