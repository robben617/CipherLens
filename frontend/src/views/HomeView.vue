<template>
  <main class="home">
    <!-- ① 项目介绍块：做什么、为了什么 -->
    <section class="hero" aria-labelledby="hero-title">
      <div class="hero__text">
        <p class="hero__eyebrow">AES-128 · 逐步可视化</p>

        <h1 id="hero-title" class="hero__title">把 AES 拆开给你看。</h1>

        <p class="hero__lede">
          CipherLens 是一个 AES 学习工具。它把一次加密拆成 40 步，逐步展示每个字节怎么变、为什么变。
        </p>

        <p class="hero__lede">
          目的是让你不只“看得见”，还能自己算对、讲得清。卡住时，能知道卡在第几步、哪个字节。
        </p>

        <p class="hero__lede hero__lede--soft">
          不需要先学完数学——遇到哪一步，再讲哪一步的数学。
        </p>

        <div class="hero__cta">
          <RouterLink class="btn btn--primary" to="/workbench">看一次真实的加密</RouterLink>

          <a class="btn btn--ghost" href="/aes-quest/index.html">进入像素闯关记</a>
        </div>
      </div>

      <div class="hero__demo">
        <HeroMatrix />
      </div>
    </section>

    <!-- ② AES 简介块：AES 是什么 -->
    <section class="sec aes" aria-labelledby="aes-title">
      <h2 id="aes-title" class="sec__title">AES 是什么</h2>

      <p class="aes__body">
        AES 是一种分组密码，把数据按 16 字节一组加密。同一段明文，换一个密钥就会得到不同密文；它是今天最常用的对称加密算法之一。
      </p>

      <p class="aes__body">
        本项目以 AES-128 为例，把从明文到密文的每一步变换完整展示出来。
      </p>
    </section>

    <footer class="foot">
      <span>仅用于学习 AES 原理，不用于加密真实数据</span>
      <span class="foot__ver">v0.1</span>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { RouterLink } from 'vue-router'
import HeroMatrix from '../components/home/HeroMatrix.vue'
</script>

<style scoped>
.home {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--sp-16) var(--sp-6) var(--sp-8);
}

/* ============ ① 项目介绍块 ============ */
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
  gap: var(--sp-4);
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

/* ============ ② AES 简介块 ============ */
.sec {
  margin-top: var(--sp-16);
}

.sec__title {
  margin: 0 0 var(--sp-4);
  font-family: var(--font-display);
  font-size: var(--fs-h1);
  font-weight: 600;
  line-height: var(--lh-snug);
  color: var(--ink-1);
}

.aes__body {
  margin: 0 0 var(--sp-3);
  max-width: 32rem;
  font-size: 1rem;
  line-height: 1.75;
  color: var(--ink-2);
}

/* ============ 页脚 ============ */
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
}

@media (max-width: 700px) {
  .home {
    padding-top: var(--sp-8);
  }

  .btn {
    width: 100%;
  }
}
</style>