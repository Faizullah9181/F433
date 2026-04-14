import { Streamdown } from "streamdown";

interface MarkdownContentProps {
  content: string;
  className?: string;
}

export function MarkdownContent({ content, className = "" }: MarkdownContentProps) {
  const normalized = content
    // Remove fenced code markers so content renders as plain prose.
    .replace(/```[a-zA-Z0-9_-]*\n?/g, "")
    .replace(/```/g, "");

  return (
    <div className={`md-content ${className}`.trim()}>
      <Streamdown
        mode="static"
        components={{
          pre: ({ children }) => <p>{children}</p>,
          code: ({ children }) => <span>{children}</span>,
        }}
      >
        {normalized}
      </Streamdown>
    </div>
  );
}
