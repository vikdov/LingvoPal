// Simple two-line incorrect feedback — no diff engine.
// Caller renders userAnswer in red and correctAnswer in green below the sentence.
export function getIncorrectFeedback(
  userAnswer: string,
  correctAnswer: string,
): { userAnswer: string; correctAnswer: string } {
  return { userAnswer: userAnswer.trim(), correctAnswer: correctAnswer.trim() };
}
