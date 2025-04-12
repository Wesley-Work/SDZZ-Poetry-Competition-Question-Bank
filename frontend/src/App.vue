<template>
  <div class="app-container">
    <t-layout>
      <t-header>
        <h1 style="margin: 0.82em">顺德中专、技工学校 2025年诗词大会 比赛题库</h1>
      </t-header>

      <t-content>
        <t-card class="poetry-card" @click="showAnswerIfHidden">
          <template #header>
            <div class="card-header">
              <span>随机诗词题目</span>
              <t-button theme="primary" @click.stop="nextQuestion">下一题</t-button>
            </div>
          </template>

          <div v-if="currentPoem" class="poetry-content">
            <h2>《{{ currentPoem.poem.title }}》</h2>
            <p class="author">{{ currentPoem.poem.author }}（{{ currentPoem.poem.dynasty }}）</p>
            <div class="question">
              <p v-if="currentPoem">{{ currentPoem.poem.question }}</p>
            </div>
            <div v-if="showAnswer" class="answer">
              <p>答案：{{ currentPoem.poem.answer }}</p>
            </div>
          </div>
          <div v-else class="no-poetry">
            <p>暂无诗词题目</p>
          </div>
        </t-card>
      </t-content>
    </t-layout>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { MessagePlugin } from 'tdesign-vue-next';

interface Poem {
  poem: {
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
  };
}

const poems = ref<Poem[]>([]);
const currentPoem = ref<Poem | null>(null);
const showAnswer = ref(false);

const fetchPoems = async () => {
  try {
    const response = await axios.get('http://localhost:3000/api/poems');
    poems.value = response.data.poems;
    if (poems.value.length > 0) {
      selectRandomPoem();
    }
  } catch (error) {
    MessagePlugin.error('获取诗词列表失败');
  }
};

const selectRandomPoem = async () => {
  try {
    const response = await axios.get('http://localhost:3000/api/poems/random');
    currentPoem.value = response.data;
    showAnswer.value = false;
  } catch (error) {
    MessagePlugin.error('获取随机诗词失败');
  }
};

const showAnswerIfHidden = () => {
  if (!showAnswer.value) {
    showAnswer.value = true;
  }
};

const nextQuestion = () => {
  selectRandomPoem();
};

onMounted(() => {
  fetchPoems();
});
</script>

<style scoped>
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
  text-align: center;
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
  margin-top: 20px;
  padding: 15px;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.no-poetry {
  text-align: center;
  color: #666;
  padding: 20px;
}
</style>
