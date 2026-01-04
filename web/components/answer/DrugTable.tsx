import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';

interface TableCell {
  value: string;
  alignment?: 'left' | 'center' | 'right';
  emphasis?: boolean;
  color?: string;
  tooltip?: string;
}

interface TableRow {
  cells: TableCell[];
  isHeader?: boolean;
}

interface DrugTableProps {
  id: string;
  title?: string;
  caption?: string;
  headers: string[];
  rows: TableRow[];
  sortable?: boolean;
  filterable?: boolean;
  footer?: string;
  className?: string;
}

export const DrugTable: React.FC<DrugTableProps> = ({
  id,
  title,
  caption,
  headers,
  rows,
  sortable = true,
  filterable = false,
  footer,
  className,
}) => {
  const [sortColumn, setSortColumn] = useState<number | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filter, setFilter] = useState('');

  const handleSort = (columnIndex: number) => {
    if (!sortable) return;

    if (sortColumn === columnIndex) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnIndex);
      setSortDirection('asc');
    }
  };

  const sortedRows = React.useMemo(() => {
    if (sortColumn === null) return rows;

    return [...rows].sort((a, b) => {
      const aVal = a.cells[sortColumn]?.value || '';
      const bVal = b.cells[sortColumn]?.value || '';

      const comparison = aVal.localeCompare(bVal, undefined, { numeric: true });
      return sortDirection === 'asc' ? comparison : -comparison;
    });
  }, [rows, sortColumn, sortDirection]);

  const filteredRows = React.useMemo(() => {
    if (!filter) return sortedRows;

    return sortedRows.filter((row) =>
      row.cells.some((cell) => cell.value.toLowerCase().includes(filter.toLowerCase()))
    );
  }, [sortedRows, filter]);

  return (
    <div className={cn('w-full overflow-hidden rounded-lg border border-gray-200', className)}>
      {title && (
        <div className="bg-gray-50 px-4 py-3 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          {caption && <p className="text-sm text-gray-600 mt-1">{caption}</p>}
        </div>
      )}

      {filterable && (
        <div className="px-4 py-2 bg-white border-b border-gray-200">
          <input
            type="text"
            placeholder="Filter table..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="w-full px-3 py-1.5 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>
      )}

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 border-b border-gray-200">
            <tr>
              {headers.map((header, index) => (
                <th
                  key={index}
                  onClick={() => handleSort(index)}
                  className={cn(
                    'px-4 py-3 text-left font-semibold text-gray-700',
                    sortable && 'cursor-pointer hover:bg-gray-100 select-none'
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span>{header}</span>
                    {sortable && (
                      <span className="text-gray-400">
                        {sortColumn === index ? (
                          sortDirection === 'asc' ? (
                            <ArrowUp className="w-4 h-4" />
                          ) : (
                            <ArrowDown className="w-4 h-4" />
                          )
                        ) : (
                          <ArrowUpDown className="w-4 h-4" />
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {filteredRows.map((row, rowIndex) => (
              <tr key={rowIndex} className="hover:bg-gray-50 transition-colors">
                {row.cells.map((cell, cellIndex) => {
                  const alignmentClass =
                    cell.alignment === 'center'
                      ? 'text-center'
                      : cell.alignment === 'right'
                      ? 'text-right'
                      : 'text-left';

                  return (
                    <td
                      key={cellIndex}
                      className={cn('px-4 py-3', alignmentClass)}
                      style={{ backgroundColor: cell.color }}
                      title={cell.tooltip}
                    >
                      <span className={cn(cell.emphasis && 'font-semibold text-gray-900')}>
                        {cell.value}
                      </span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {footer && (
        <div className="px-4 py-2 bg-gray-50 border-t border-gray-200 text-xs text-gray-600">
          {footer}
        </div>
      )}
    </div>
  );
};
