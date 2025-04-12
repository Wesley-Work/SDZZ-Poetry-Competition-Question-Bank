// 抽取诗词 v2版本
// 整首诗随机抽某段

import Router from 'koa-router';
import { Context } from 'koa';
import fs from 'fs';
import path from 'path';
import poems from '../data/poems_v2.json';
import { loadPoems } from '../utils/poemLoader';
import { canCross as canCrossConfig, allowRandomHalfSentence } from '../config';

interface Poem {
  id: number;
  title: string;
  author: string;
  content: string;
  dynasty: string;
  type: string;
  tags: string[];
}

interface PoemsData {
  poems: Poem[];
}

const router = new Router({
  prefix: '/api/poems',
});
const dataPath = path.join(__dirname, '../data/poems.json');

// 获取随机诗词
router.get('/random', async (ctx) => {
  try {
    // 诗词列表
    const poems = await loadPoems();
    // 随机诗键
    const randomPoemIndex = Math.floor(Math.random() * poems.length);
    // 随机诗词
    const selectedPoem = poems[randomPoemIndex];
    const { content } = selectedPoem;

    // 将诗词内容按句分割，并保留标点符号
    const sentences = content.match(/[^。！？]+[。！？]/g) || [];

    // 随机选择一句或跨句
    let selectedSentence;
    if (canCrossConfig && sentences.length > 1) {
      // 随机选择起始句
      const startIndex = Math.floor(Math.random() * (sentences.length - 1));
      // 随机选择是否跨句
      const cross = Math.random() > 0.5;
      if (cross) {
        selectedSentence = sentences[startIndex] + sentences[startIndex + 1];
      } else {
        selectedSentence = sentences[startIndex];
      }
    } else {
      // 不跨句，随机选择一句
      const randomSentenceIndex = Math.floor(Math.random() * sentences.length);
      selectedSentence = sentences[randomSentenceIndex];
    }

    // 将选中的句子按逗号分割
    const parts = selectedSentence.split(/[，、]/);
    // 随机选择一部分作为题目
    const randomPartIndex = Math.floor(Math.random() * parts.length);
    const questionPart = parts[randomPartIndex];

    // 生成题目和答案
    const question = selectedSentence.replace(questionPart, questionPart.replace(/[\u4e00-\u9fa5]/g, '__'));
    // 保持原文结尾符号
    const ending = (selectedSentence.match(/[。！？]/) || [''])[0];
    const questionWithEnding = question + (question[question.length - 1] === ending ? '' : ending);

    // 返回结果格式调整
    ctx.body = {
      poem: {
        ...selectedPoem,
        question: questionWithEnding, // 或者使用 questionWithDoubleUnderscore
        answer: questionPart,
      },
    };
  } catch (error) {
    console.error('Error in /random route:', error);
    ctx.status = 500;
    ctx.body = { error: '获取随机诗词失败' };
  }
});

// 获取所有诗词
router.get('/', async (ctx) => {
  try {
    ctx.body = poems;
  } catch (error) {
    console.error('Error in GET / route:', error);
    ctx.status = 500;
    ctx.body = { error: '获取诗词列表失败' };
  }
});

// 获取单个诗词
router.get('/:id', async (ctx: Context) => {
  try {
    const data = fs.readFileSync(dataPath, 'utf8');
    const poems = JSON.parse(data).poems;
    const poem = poems.find((p: Poem) => p.id === parseInt(ctx.params.id));

    if (poem) {
      ctx.body = poem;
    } else {
      ctx.status = 404;
      ctx.body = { error: '未找到该诗词' };
    }
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: '读取诗词数据失败' };
  }
});

// 添加新诗词
router.post('/', async (ctx: Context) => {
  try {
    const data = fs.readFileSync(dataPath, 'utf8');
    const poems = JSON.parse(data) as PoemsData;
    const newPoem = ctx.request.body as Poem;

    newPoem.id = poems.poems.length + 1;
    poems.poems.push(newPoem);

    fs.writeFileSync(dataPath, JSON.stringify(poems, null, 2));
    ctx.status = 201;
    ctx.body = newPoem;
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: '添加诗词失败' };
  }
});

export default router;
