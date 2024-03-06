import { Module } from '@nestjs/common';
// import { TelegramController } from './app.controller';
// import { AppService } from './app.service';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TelegramEntity } from './telegram/telegram.entity';
import { CodeService } from './code_service';
import { TelegramService } from './app.controller';
import { SendCodeTelegramService } from './send_code_telegram';
import { TelegramModule } from './telegram.module';
import { ConfigModule } from '@nestjs/config';

@Module({
  imports: [
    ConfigModule.forRoot({
      isGlobal: true,
    }),
    TypeOrmModule.forRoot({
      type: 'postgres',
      host: process.env.DB_HOST,
      port: 5432,
      password: process.env.DB_PASSWORD,
      username: process.env.DB_USER,
      entities: [TelegramEntity],
      database: process.env.DB_NAME,
      logging: true,
      synchronize: false,
    }),
    TelegramModule,
  ],
  controllers: [],
  providers: [],
})
export class AppModule {}
