// src/models/EmailModel.ts

export interface EmailModel {
  subject: string;
  sender: string; // full sender email address, e.g. "ceo@company.com"
  body: string;

  // Optional fields (populate from Outlook item if available)
  senderDisplayName?: string;
  links?: string[]; // extracted links (if you already extract them in the add-in)
  attachments?: string[]; // attachment filenames, e.g. ["invoice.pdf", "update.zip"]
}