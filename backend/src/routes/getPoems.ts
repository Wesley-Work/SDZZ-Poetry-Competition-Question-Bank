import Router from 'koa-router';
import { Context } from 'koa';
import { loadPoems, loadPoemsSentences } from '../utils/poemLoader';
import { poemSlice } from '../utils/poemSlice';

const router = new Router({
  prefix: '/api',
});

// 获取随机一首诗词
router.all('/pick-one', async (ctx: Context) => {
  try {
    const poems = await loadPoems();
    const randomKey = Math.floor(Math.random() * poems.length);
    const poem = poems[randomKey];

    if (poem) {
      ctx.body = poem;
    } else {
      ctx.body = { error: '未找到该诗词' };
    }
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: '读取诗词数据失败', data: error };
  }
});

// 获取全部诗词
router.all('/pick-all', async (ctx: Context) => {
  try {
    const poems = await loadPoems();

    if (poems) {
      ctx.body = poems;
    } else {
      ctx.body = { error: '无诗词内容' };
    }
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: '读取诗词数据失败', data: error };
  }
});

// 获取随机诗词
router.all('/pick-random', async (ctx: Context) => {
  try {
    const bodyParams: any = ctx.request.body;
    // 是不是跨句
    const { canCross } = bodyParams;
    // const canCross = Math.random() > 0.5;
    // 上句还是下句
    const isNext = Math.random() > 0.5;
    // 诗词类型，整首诗还是句子
    const isWhole = Math.random() > 0.5;
    // 诗词列表
    const poems = isWhole ? await loadPoems() : await loadPoemsSentences();
    // 诗词随机key
    const randomKey = Math.floor(Math.random() * poems.length);
    // 诗词句
    const poem = poems[randomKey];

    const qa = poemSlice(poem?.content, isNext, canCross, isWhole);

    const tent = {
      poem: poem,
      isWhole: isWhole,
      sourceIsNext: isNext,
      canCross: canCross,
      ...qa,
    };

    if (tent) {
      ctx.body = tent;
    } else {
      ctx.body = { error: '无诗词内容' };
    }
  } catch (error) {
    ctx.status = 500;
    ctx.body = { error: '读取诗词数据失败', data: error };
  }
});

export default router;
