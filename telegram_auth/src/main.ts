import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
export let telegramToken: string = '';
async function bootstrap() {
  telegramToken = process.env.TG_AUTH_BOT_TOKEN;
  console.log(telegramToken);
  const app = await NestFactory.create(AppModule);
  await app.listen(3113);
}
bootstrap();
