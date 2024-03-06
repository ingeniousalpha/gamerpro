import { Column, Entity, PrimaryGeneratedColumn } from 'typeorm';

@Entity({
  name: 'authentication_tgauthuser',
})
export class TelegramEntity {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'varchar' })
  mobile_phone: string;

  @Column({ type: 'int' })
  chat_id: number;
}
