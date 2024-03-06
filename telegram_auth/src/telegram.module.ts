import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { TelegramEntity } from './telegram/telegram.entity';
import { CodeService } from './code_service';
import { TelegramService } from './app.controller';
import { SendCodeTelegramService } from './send_code_telegram';
import { TelegramController } from './telegram_controller';

@Module({
  imports: [TypeOrmModule.forFeature([TelegramEntity])],
  providers: [CodeService, TelegramService, SendCodeTelegramService],
  controllers: [TelegramController],
})
export class TelegramModule {}
