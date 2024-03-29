import { HttpException, HttpStatus, Inject, Injectable } from '@nestjs/common';
import { CodeService, cleanPhoneNumber } from './code_service';
import { telegramBot } from './app.controller';
import { InjectRepository } from '@nestjs/typeorm';
import { TelegramEntity } from './telegram/telegram.entity';
import { Repository } from 'typeorm';

@Injectable()
export class SendCodeTelegramService {
  constructor(
    @InjectRepository(TelegramEntity)
    private readonly telegramRepository: Repository<TelegramEntity>,
    private codeSerivce: CodeService,
    // private configService: ConfigService,
  ) {}

  async sendCode(__: { phoneNumber: string }): Promise<boolean> {
    const phoneNumber = cleanPhoneNumber(__.phoneNumber);
    const entity = await this.telegramRepository.findOne({
      where: {
        mobile_phone: phoneNumber,
      },
    });

    if (entity == null)
      throw new HttpException('Not found user', HttpStatus.NOT_FOUND);
    const verifyCode = this.codeSerivce.generateCode(phoneNumber);
    telegramBot.sendMessage(
      entity.chat_id,
      `По номеру ${phoneNumber}, ваш код верификации: <b>${verifyCode}</b>\n\nВведите этот код в приложении.`,
      {parse_mode : "HTML"}
    );
    return true;
  }
}
