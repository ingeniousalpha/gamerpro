import { Controller, Get, Injectable } from '@nestjs/common';

import { InjectRepository } from '@nestjs/typeorm';
import { TelegramEntity } from './telegram/telegram.entity';
import { Repository } from 'typeorm';
import * as TelegramBot from 'node-telegram-bot-api';
import { CodeService, cleanPhoneNumber } from './code_service';
import { telegramToken } from './main';

// const accessTokenTelegram = telegramToken;

export let telegramBot: TelegramBot;

@Injectable()
export class TelegramService {
  constructor(
    @InjectRepository(TelegramEntity)
    private readonly telegramRepository: Repository<TelegramEntity>,
    private codeSerivce: CodeService,
  ) {
    telegramBot = new TelegramBot(telegramToken, {
      polling: true,
    });
    this.init();
  }
  async init() {
    telegramBot.on(
      'message',
      (message: TelegramBot.Message, metadata: TelegramBot.Metadata) =>
        this.onMessage(message, metadata),
    );
  }

  async onMessage(
    message: TelegramBot.Message,
    metadata: TelegramBot.Metadata,
  ) {
    try {
      if (message.text == '/start') {
        this.setKeyboard(message, metadata);
        return;
      }
      if (metadata.type == 'contact') {
        if (message.contact.user_id != message.from.id) {
          telegramBot.sendMessage(message.chat.id, `Это не ваш номер телефона`);
          return;
        }
        const phoneNumber = cleanPhoneNumber(message.contact.phone_number);
        const founded = await this.telegramRepository.findOne({
          where: {
            mobile_phone: phoneNumber,
          },
        });
        if (founded) {
          await this.telegramRepository.update(
            {
              mobile_phone: phoneNumber,
            },
            {
              chat_id: message.chat.id,
              mobile_phone: phoneNumber,
            },
          );
        } else {
          await this.telegramRepository.insert({
            chat_id: message.chat.id,
            mobile_phone: phoneNumber,
          });
        }

        const verifyCode = this.codeSerivce.generateCode(phoneNumber);
        telegramBot
          .sendMessage(
            message.chat.id,
            `Можете продолжить верификацию в приложении.\nВаш код верификации ${verifyCode} для номера +${phoneNumber}`,
          )
          .catch((e) => console.log(e));
      }
    } catch (e) {
      console.log(e);
    }
  }

  async setKeyboard(
    message: TelegramBot.Message,
    metadata: TelegramBot.Metadata,
  ) {
    try {
      await telegramBot.sendMessage(
        message.chat.id,
        'Как мы можем с вами связаться ?',
        {
          parse_mode: 'Markdown',
          reply_markup: {
            one_time_keyboard: true,
            keyboard: [
              [
                {
                  text: 'Номер телефона',
                  request_contact: true,
                },
              ],
            ],
          },
        },
      );
    } catch (e) {
      console.log(e);
    }
  }
}
