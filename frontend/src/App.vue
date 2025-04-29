<template>
  <div class="container">
    <div class="app-container">
      <t-layout style="background: #eeeeee33">
        <div style="background-color: var(--td-bg-color-container)">
          <h1
            style="margin: 0.82em"
            @click="
              () => {
                showConfig = !showConfig;
              }
            "
          >
            顺德中专、技工学校 2025年诗词大会 比赛题库
          </h1>
          <t-space v-if="showConfig" style="margin-left: 0.82em; margin-bottom: 0.41em">
            <span>当前模式：{{ currentMode === 'random' ? '随机题目' : '顺序题目' }}</span>
            <span>
              <t-tag variant="light-outline" :theme="canCross ? 'primary' : 'error'">{{
                canCross ? '允许跨句' : '禁止跨句'
              }}</t-tag>
            </span>
            <t-space v-if="poems">
              <span>是否为下一句：{{ poems.isNext }}</span>
              <span>是否为整首诗：{{ poems.isWhole }}</span>
              <span>原始_是否为下一句：{{ poems.sourceIsNext }}</span>
            </t-space>
          </t-space>
        </div>

        <t-content>
          <t-card class="poetry-card" @click="handleShowAnswer">
            <!-- <template #header>
              <div class="card-header">
                <t-button theme="primary" @click.stop="getRandomPoems">下一题</t-button>
              </div>
            </template> -->

            <div v-if="currentPoem" class="poetry-content">
              <!---->
              <h2>《{{ currentPoem.title }}》</h2>
              <p class="author">{{ currentPoem.author }}（{{ currentPoem.dynasty }}）</p>
              <div class="question">
                <p v-if="currentPoem && poems">{{ poems.question }}</p>
              </div>
              <div v-if="showAnswer" class="answer">
                <p>答案：{{ poems?.answer }}</p>
              </div>
              <!---->
              <div class="next">
                <div @click.stop="getRandomPoems">
                  <CaretRightIcon style="width: 24px; height: 24px" />
                </div>
              </div>
              <!---->
            </div>
            <div v-else class="no-poetry">
              <p>暂无诗词题目</p>
            </div>
          </t-card>
        </t-content>
      </t-layout>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { MessagePlugin, NotifyPlugin } from 'tdesign-vue-next';
import { CaretRightIcon } from 'tdesign-icons-vue-next';
import { api, canCross } from './config';

interface Poem {
  id: number;
  title: string;
  author: string;
  content: string;
  dynasty: string;
  type: string;
  tags: string[];
  hasComma: boolean;
  question: string;
  answer: string;
}

interface Poems {
  answer: string;
  canCross: boolean;
  isNext: boolean;
  isWhole: boolean;
  mode: 'sentences' | 'whole';
  poem: Poem;
  question: string;
  sourceIsNext: boolean;
}

const poems = ref<Poems>();
const currentPoem = ref<Poem | null>(null);
const currentMode = ref('random');
const showAnswer = ref(false);
const showConfig = ref(false);

const getRandomPoems = () => {
  showAnswer.value = false;
  fetch(api + '/pick-random', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      canCross,
    }),
  })
    .then((res) => {
      if (res.status !== 200) {
        MessagePlugin.error('获取诗词题目失败');
        return new Error('Network response was not ok.');
      }
      return res.json();
    })
    .then((res: Poems) => {
      poems.value = res;
      currentPoem.value = res.poem;
    })
    .catch((err) => {
      NotifyPlugin.error({
        title: '错误',
        content: '获取诗词题目失败：' + err,
        duration: 2000,
      });
    });
};

const handleShowAnswer = () => {
  showAnswer.value = true;
};

onMounted(() => {
  getRandomPoems();
});
</script>

<style lang="scss">
html,
body {
  margin: 0;
}

.container {
  position: relative;
  height: 100vh;
  width: 100vw;
  z-index: 0;
}

.container::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-image: url(./assets/background.jpg);
  background-size: contain;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0.5;
  z-index: -1;
}

.app-container {
  padding: 20px;
  margin: 0 auto;
}

.t-header {
  background-color: #0052d9;
  color: white;
  text-align: center;
  line-height: 64px;
  margin-bottom: 20px;
}

.poetry-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.poetry-content {
  position: relative;
  text-align: center;
  padding: 24px 0;
  .next {
    position: absolute;
    top: 0;
    right: 0;
    height: 100%;
    width: 68px;
    opacity: 0;
    transition: all 0.28s ease-in-out;
    border-radius: 4px;
    &:hover {
      opacity: 1;
      background: var(--td-bg-color-container-hover);
    }

    > div {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
    }
  }
}

.author {
  color: #666;
  margin: 10px 0;
}

.question {
  font-size: 1.2em;
  margin: 20px 0;
  line-height: 1.8;
}

.answer {
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
  padding: 15px;
  width: 88%;
  margin: 20px auto 0;
}

.no-poetry {
  text-align: center;
  color: #666;
  padding: 20px;
}
</style>
