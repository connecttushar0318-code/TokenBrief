"use client";

import { useEffect, useState } from "react";
import {
  AlertCircle,
  Award,
  CheckCircle2,
  Clock,
  HelpCircle,
  Play,
  RotateCcw,
  Sliders,
  Sparkles,
  XCircle,
} from "lucide-react";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface QuizQuestion {
  id: number;
  document_id: number;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  source_page_number: number | null;
  difficulty: string;
}

interface AnswerResult {
  question_id: number;
  question_text: string;
  selected_option: string;
  correct_option: string;
  is_correct: boolean;
  explanation?: string;
  source_page_number?: number;
}

interface QuizAttemptResult {
  attempt_id: number;
  document_id: number;
  total_questions: number;
  correct_count: number;
  score_percentage: number;
  answers: AnswerResult[];
  completed_at: string;
}

interface DocumentItem {
  id: number;
  filename: string;
}

export function InteractiveQuizStudio({
  apiBaseUrl,
  documents,
  initialDocId,
}: {
  apiBaseUrl: string;
  documents: DocumentItem[];
  initialDocId?: number | null;
}) {
  const [selectedDocId, setSelectedDocId] = useState<number | null>(
    initialDocId || (documents[0]?.id ?? null)
  );
  const [questionCount, setQuestionCount] = useState<number>(5);
  const [difficulty, setDifficulty] = useState<string>("medium");
  const [isGenerating, setIsGenerating] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [questions, setQuestions] = useState<QuizQuestion[]>([]);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, string>>({});
  const [quizResult, setQuizResult] = useState<QuizAttemptResult | null>(null);
  const [isReviewMode, setIsReviewMode] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!selectedDocId && documents.length > 0) {
      setSelectedDocId(documents[0].id);
    }
  }, [documents, selectedDocId]);

  const handleGenerateQuiz = async (reviewMode = false) => {
    if (!selectedDocId) return;
    setIsGenerating(true);
    setErrorMessage(null);
    setQuizResult(null);
    setSelectedAnswers({});
    setIsReviewMode(reviewMode);

    try {
      if (reviewMode) {
        const res = await fetch(`${apiBaseUrl}/api/quiz/spaced-review/${selectedDocId}`, {
          credentials: "include",
        });
        if (!res.ok) throw new Error("Failed to load review questions.");
        const data = await res.json();
        if (data.length === 0) {
          throw new Error("No previous mistakes found for this document! Generate a fresh quiz first.");
        }
        setQuestions(data);
      } else {
        const res = await fetch(`${apiBaseUrl}/api/quiz/generate`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          credentials: "include",
          body: JSON.stringify({
            document_id: selectedDocId,
            number_of_questions: questionCount,
            difficulty,
          }),
        });
        if (!res.ok) throw new Error("Quiz generation failed. Check document indexing.");
        const data = await res.json();
        setQuestions(data);
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Could not generate quiz.");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSelectOption = (questionId: number, optionLetter: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionLetter,
    }));
  };

  const handleSubmitQuiz = async () => {
    if (!selectedDocId || questions.length === 0) return;
    setIsSubmitting(true);
    setErrorMessage(null);

    const formattedAnswers = questions.map((q) => ({
      question_id: q.id,
      selected_option: selectedAnswers[q.id] || "A",
    }));

    try {
      const res = await fetch(`${apiBaseUrl}/api/quiz/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          document_id: selectedDocId,
          answers: formattedAnswers,
        }),
      });
      if (!res.ok) throw new Error("Failed to submit and grade quiz.");
      const resultData = await res.json();
      setQuizResult(resultData);
    } catch (err: any) {
      setErrorMessage(err.message || "Failed to submit answers.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const answeredCount = Object.keys(selectedAnswers).length;

  return (
    <div className="space-y-6">
      <Card className="border-border/80 bg-card/60">
        <CardHeader className="pb-4">
          <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <CardTitle className="text-xl flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-primary" />
                <span>AI Exam &amp; Quiz Engine</span>
              </CardTitle>
              <CardDescription className="text-xs">
                Generate grounded multiple-choice tests directly from your indexed PDFs
              </CardDescription>
            </div>
            {questions.length > 0 && !quizResult && (
              <Badge variant="outline" className="text-xs font-mono w-fit">
                Answered: {answeredCount} / {questions.length}
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                Target Document
              </label>
              <select
                value={selectedDocId || ""}
                onChange={(e) => {
                  setSelectedDocId(Number(e.target.value));
                  setQuestions([]);
                  setQuizResult(null);
                }}
                className="w-full text-xs rounded-lg border border-border bg-background px-3 py-2 text-foreground focus:outline-none focus:ring-1 focus:ring-primary"
              >
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs font-medium text-muted-foreground mb-1.5">
                <span className="flex items-center gap-1.5">
                  <Sliders className="h-3.5 w-3.5" />
                  Questions: <span className="font-bold text-foreground">{questionCount}</span>
                </span>
                <span className="text-[10px]">3 - 15</span>
              </div>
              <input
                type="range"
                min="3"
                max="15"
                step="1"
                value={questionCount}
                onChange={(e) => setQuestionCount(Number(e.target.value))}
                className="w-full accent-primary cursor-pointer"
              />
            </div>

            <div>
              <label className="text-xs font-medium text-muted-foreground block mb-1.5">
                Difficulty Level
              </label>
              <div className="grid grid-cols-3 gap-1 rounded-lg border border-border p-1 bg-muted/30">
                {["easy", "medium", "hard"].map((lvl) => (
                  <button
                    key={lvl}
                    type="button"
                    onClick={() => setDifficulty(lvl)}
                    className={`text-xs py-1 rounded capitalize font-medium transition-colors ${
                      difficulty === lvl
                        ? "bg-card text-foreground shadow-sm"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    {lvl}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {errorMessage && (
            <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          )}

          <div className="flex flex-wrap gap-2.5 pt-1">
            <Button
              onClick={() => handleGenerateQuiz(false)}
              disabled={isGenerating || !selectedDocId}
              className="gap-2 text-xs"
            >
              <Play className={`h-3.5 w-3.5 ${isGenerating ? "animate-spin" : ""}`} />
              <span>{isGenerating ? "Generating Grounded MCQs..." : "Generate New Quiz"}</span>
            </Button>

            <Button
              variant="outline"
              onClick={() => handleGenerateQuiz(true)}
              disabled={isGenerating || !selectedDocId}
              className="gap-2 text-xs"
              title="Review questions previously answered incorrectly"
            >
              <RotateCcw className="h-3.5 w-3.5 text-amber-500" />
              <span>Spaced Repetition Review</span>
            </Button>
          </div>
        </CardContent>
      </Card>

      {quizResult && (
        <Card className="border-border/80 bg-gradient-to-br from-card/90 via-card/60 to-primary/5">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                  <Award className="h-6 w-6" />
                </div>
                <div>
                  <CardTitle className="text-lg">Assessment Graded</CardTitle>
                  <CardDescription className="text-xs">
                    {quizResult.correct_count} of {quizResult.total_questions} questions correct
                  </CardDescription>
                </div>
              </div>
              <div className="text-right">
                <span className="text-3xl font-black text-primary">
                  {quizResult.score_percentage}%
                </span>
                <p className="text-[11px] text-muted-foreground">
                  {quizResult.score_percentage >= 70 ? "Mastery Demonstrated 🎉" : "Needs Review 📚"}
                </p>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              Detailed Question Analysis &amp; Citations
            </h4>
            <div className="space-y-3">
              {quizResult.answers.map((ans, idx) => (
                <div
                  key={ans.question_id}
                  className={`p-3.5 rounded-xl border text-xs space-y-2 ${
                    ans.is_correct
                      ? "bg-emerald-500/5 border-emerald-500/20"
                      : "bg-destructive/5 border-destructive/20"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <p className="font-semibold leading-relaxed">
                      {idx + 1}. {ans.question_text}
                    </p>
                    {ans.is_correct ? (
                      <Badge variant="secondary" className="bg-emerald-500/10 text-emerald-600 shrink-0 text-[10px] gap-1">
                        <CheckCircle2 className="h-3 w-3" /> Correct
                      </Badge>
                    ) : (
                      <Badge variant="destructive" className="shrink-0 text-[10px] gap-1">
                        <XCircle className="h-3 w-3" /> Incorrect
                      </Badge>
                    )}
                  </div>
                  <div className="flex flex-wrap gap-4 text-muted-foreground font-mono">
                    <span>Your choice: <b className="text-foreground">{ans.selected_option}</b></span>
                    <span>Correct answer: <b className="text-emerald-500">{ans.correct_option}</b></span>
                    {ans.source_page_number && (
                      <Badge variant="outline" className="text-[10px]">
                        Grounded on Page {ans.source_page_number}
                      </Badge>
                    )}
                  </div>
                  {ans.explanation && (
                    <p className="text-muted-foreground pt-1 border-t border-border/40 text-[11px]">
                      <b>Explanation:</b> {ans.explanation}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {questions.length > 0 && !quizResult && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold flex items-center gap-2">
              <HelpCircle className="h-4 w-4 text-primary" />
              <span>Interactive Quiz Questions ({questions.length})</span>
            </h3>
            {isReviewMode && (
              <Badge variant="secondary" className="text-[10px] bg-amber-500/10 text-amber-600">
                Spaced Review Mode
              </Badge>
            )}
          </div>

          <div className="space-y-4">
            {questions.map((q, idx) => {
              const selectedOpt = selectedAnswers[q.id];
              return (
                <Card key={q.id} className="border-border/80 bg-card/60">
                  <CardHeader className="pb-2">
                    <div className="flex items-start justify-between gap-3">
                      <CardTitle className="text-sm font-semibold leading-relaxed">
                        <span className="text-primary font-mono mr-1.5">Q{idx + 1}.</span>
                        {q.question_text}
                      </CardTitle>
                      {q.source_page_number && (
                        <Badge variant="outline" className="text-[10px] shrink-0">
                          Page {q.source_page_number}
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-2 pt-1">
                    {[
                      { key: "A", text: q.option_a },
                      { key: "B", text: q.option_b },
                      { key: "C", text: q.option_c },
                      { key: "D", text: q.option_d },
                    ].map(({ key, text }) => {
                      const isSelected = selectedOpt === key;
                      return (
                        <button
                          key={key}
                          type="button"
                          onClick={() => handleSelectOption(q.id, key)}
                          className={`w-full text-left p-3 rounded-lg border text-xs transition-all flex items-start gap-3 ${
                            isSelected
                              ? "bg-primary/10 border-primary text-foreground font-medium shadow-sm"
                              : "border-border/60 hover:bg-muted/40 text-muted-foreground hover:text-foreground"
                          }`}
                        >
                          <span
                            className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-bold ${
                              isSelected ? "bg-primary text-white" : "bg-muted text-muted-foreground"
                            }`}
                          >
                            {key}
                          </span>
                          <span className="leading-snug pt-0.5">{text}</span>
                        </button>
                      );
                    })}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          <div className="flex justify-end pt-2">
            <Button
              onClick={handleSubmitQuiz}
              disabled={isSubmitting}
              className="gap-2 text-xs h-9 px-5"
            >
              <CheckCircle2 className="h-4 w-4" />
              <span>{isSubmitting ? "Grading Responses..." : "Submit & Grade Quiz"}</span>
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
