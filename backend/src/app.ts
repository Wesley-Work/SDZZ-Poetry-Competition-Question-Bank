import Koa from 'koa';
import cors from '@koa/cors';
import bodyParser from 'koa-bodyparser';
import poemsRouter from './routes/poems_v2';

const app = new Koa();

// 使用中间件
app.use(cors());
app.use(bodyParser());

// 使用路由
app.use(poemsRouter.routes());
app.use(poemsRouter.allowedMethods());

// 错误处理
app.on('error', (err, ctx) => {
  console.error('server error', err);
});

export default app;
