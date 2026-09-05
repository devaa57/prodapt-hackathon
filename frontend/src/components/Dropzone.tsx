import { useState, type DragEvent, type ReactNode } from "react";
import { UploadCloud } from "lucide-react";

type Props = {
  label: string;
  hint: string;
  multiple?: boolean;
  accept?: string;
  onFiles: (files: File[]) => void;
  children?: ReactNode;
};

export function Dropzone({ label, hint, multiple, accept, onFiles, children }: Props) {
  const [active, setActive] = useState(false);

  function take(files: FileList | null) {
    if (!files?.length) return;
    onFiles(Array.from(files));
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setActive(false);
    take(e.dataTransfer.files);
  }

  return (
    <label
      className={`dropzone block cursor-pointer ${active ? "active" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setActive(true);
      }}
      onDragLeave={() => setActive(false)}
      onDrop={onDrop}
    >
      <UploadCloud className="mx-auto mb-3 h-8 w-8 text-accent-500" />
      <p className="font-medium text-ink-900">{label}</p>
      <p className="mt-1 text-sm text-slate-500">{hint}</p>
      {children}
      <input
        type="file"
        className="hidden"
        multiple={multiple}
        accept={accept}
        onChange={(e) => {
          take(e.target.files);
          e.target.value = "";
        }}
      />
    </label>
  );
}
