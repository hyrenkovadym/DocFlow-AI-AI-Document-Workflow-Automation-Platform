import { ReactNode } from "react";

interface Column {
  key: string;
  title: string;
  className?: string;
}

interface DataTableProps {
  columns: Column[];
  rows: Array<Record<string, ReactNode>>;
  emptyMessage: string;
}

export function DataTable({ columns, rows, emptyMessage }: DataTableProps) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm">
        <thead className="bg-slate-50 text-left text-xs uppercase tracking-wide text-slate-500">
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={`px-4 py-3 ${column.className ?? ""}`}>
                {column.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={`row-${rowIndex}`} className="border-t border-slate-100">
              {columns.map((column) => (
                <td key={`${rowIndex}-${column.key}`} className="px-4 py-3 align-top text-slate-700">
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
          {rows.length === 0 ? (
            <tr>
              <td className="px-4 py-8 text-center text-slate-500" colSpan={columns.length}>
                {emptyMessage}
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>
    </div>
  );
}
