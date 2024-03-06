import { HttpException, HttpStatus, Injectable } from '@nestjs/common';
import { Interval } from '@nestjs/schedule';
// import { cleanPhoneNumber } from 'src/utils/clean_phone_number';

export const cleanPhoneNumber = (phoneNumber: string): string => {
  return phoneNumber
    .replaceAll(' ', '')
    .replaceAll('(', '')
    .replaceAll(')', '')
    .replaceAll(',', '')
    .replaceAll('.', '')
    .trim();
    //.replaceAll('+', '')
};

function randomNumber(min, max): number {
  return Math.random() * (max - min) + min;
}

@Injectable()
export class CodeService {
  codeMap: Record<string, { code: string; date: Date }> = {};
  constructor() {}

  generateCode(_phoneNumber: string): string {
    const phoneNumber = cleanPhoneNumber(_phoneNumber);
    let code = '0000' + randomNumber(0, 10000 - 1).toString();
    code = code.slice(code.length - 4);

    this.codeMap[phoneNumber] = {
      code: code,
      date: new Date(),
    };
    console.log(code);
    return code;
  }

  verifyCode(__: { phoneNumber: string; code: string }): boolean {
    const { phoneNumber: _phoneNumber, code } = __;
    if (process.env.prod != '1' && code == '1111') return true;
    const phoneNumber = cleanPhoneNumber(_phoneNumber);

    if (!this.codeMap[phoneNumber]) {
      throw new HttpException('Not found', HttpStatus.NOT_FOUND);
    }
    const curTime = new Date().getTime();
    const entryTime = this.codeMap[phoneNumber].date.getTime();

    if (curTime - entryTime > 5 * 60 * 1000) {
      delete this.codeMap[phoneNumber];
      throw new HttpException('Not found user', HttpStatus.NOT_FOUND);
    }

    if (this.codeMap[phoneNumber].code == code) {
      return true;
    }
    throw new HttpException('Not Verified', HttpStatus.INTERNAL_SERVER_ERROR);
    // throw 'Not verified';
  }

  cleanPhoneNumber(_phoneNumber): void {
    const phoneNumber = cleanPhoneNumber(_phoneNumber);
    if (this.codeMap[phoneNumber] != null) delete this.codeMap[phoneNumber];
  }

  @Interval(1000 * 60)
  async cleanCodes() {
    const entries = Object.entries(this.codeMap);
    const curTime = new Date().getTime();
    for (const entry of entries) {
      const entryTime = entry[1].date.getTime();
      if (curTime - entryTime > 5 * 60 * 1000) {
        delete this.codeMap[entry[0]];
      }
    }
  }
}
