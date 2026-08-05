export interface EmailModel {
  subject: string;
  sender: string;
  body: string;
  links?: string[];
}