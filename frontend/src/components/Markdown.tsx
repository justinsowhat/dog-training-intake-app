import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

/** Renders assistant message text as Markdown (styled via the `.pm-md` class). */
export function Markdown({ children }: { children: string }) {
  return (
    <div className="pm-md">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Open links in a new tab.
          a: (props) => <a {...props} target="_blank" rel="noreferrer" />,
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
