import { z } from "zod";

export const loginSchema = z.object({
  username: z.string().min(2, "Username or email is required"),
  password: z.string().min(4, "Password must be at least 4 characters"),
});

export const registrationSchema = z.object({
  email: z.string().email("Invalid email address"),
  username: z
    .string()
    .min(2, "Username must be at least 2 characters")
    .max(50, "Username cannot exceed 50 characters"),
  password: z
    .string()
    .min(4, "Password must be at least 4 characters"),
});

export const documentUploadSchema = z.object({
  file: z
    .custom<File>((val) => val instanceof File, "File is required")
    .refine((file) => file.size <= 15 * 1024 * 1024, "File size exceeds 15 MB")
    .refine((file) => file.size >= 100, "File is empty (minimum 100 bytes)")
    .refine(
      (file) => {
        const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
        return [".pdf", ".txt", ".md"].includes(ext);
      },
      "Only .pdf, .txt, and .md files are supported"
    ),
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegistrationFormData = z.infer<typeof registrationSchema>;
