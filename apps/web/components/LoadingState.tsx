export function LoadingState({ message = "Loading..." }: { message?: string }) {
  return <p className="text-sm text-slate-500">{message}</p>;
}
