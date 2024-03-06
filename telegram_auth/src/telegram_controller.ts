import { Body, Controller, Post } from '@nestjs/common';
import { SendCodeTelegramService } from './send_code_telegram';
import { CodeService } from './code_service';

@Controller()
export class TelegramController {
  constructor(
    private sendCodeTelegramService: SendCodeTelegramService,

    private codeService: CodeService,
  ) {}

  @Post()
  async sendCode(@Body() body: { phoneNumber: string }) {
    return await this.sendCodeTelegramService.sendCode({
      phoneNumber: body.phoneNumber,
    });
  }
  @Post('/verify')
  async verifyCode(@Body() body: { phoneNumber: string; code: string }) {
    return this.codeService.verifyCode({
      phoneNumber: body.phoneNumber,
      code: body.code,
    });
  }
}
