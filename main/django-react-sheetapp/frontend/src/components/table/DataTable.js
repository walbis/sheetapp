import React, { useMemo } from 'react';
import EditableCell from './EditableCell';
import StatusSelect from './StatusSelect';
import Button from '../common/Button';

// Memoize Row component for performance optimization.
// It only re-renders if its specific props (row data, columns def, editing state, etc.) change.
const MemoizedRow = React.memo(({
    row,                // The data for this specific row { id, order, cells: [...], status?: '...' }
    columns,            // Array of column definitions { id, name, width, order }
    isEditing,          // Boolean: Is the table currently in edit mode?
    isTodoTable,        // Boolean: Is this a ToDo table (should show status column)?
    rowIndex,           // The index of this row in the rows array
    onCellChange,       // Callback: (rowIndex, colIndex, newValue) => void
    onDeleteRow,        // Callback: (rowId) => void
    onStatusChange      // Callback: (rowId, newStatus) => void (only for ToDo table)
}) => {
    return (
         // Add group for potential hover effects within the row
         <tr key={row.id || rowIndex} className="group hover:bg-hover-bg dark:hover:bg-gray-800">
            {/* Row Number Cell - Sticky to the left */}
            <td className="table-cell-bordered text-center align-middle p-0 h-10 leading-10 bg-background text-font-color sticky left-0 z-10 text-xs">
                {row.order}
            </td>

            {/* Status Column (Conditional) - Renders only if isTodoTable is true */}
            {isTodoTable && (
                 <td className="table-cell-bordered p-0 align-middle bg-background"> {/* No padding */}
                     <StatusSelect
                         currentStatus={row.status || 'NOT_STARTED'} // Default if status isn't set
                         rowId={row.id} // Pass row ID for identification
                         onStatusChange={onStatusChange} // Pass the handler down
                         disabled={isEditing} // Disable status change while editing structure (optional)
                     />
                 </td>
            )}

            {/* Data Cells - Map through columns to render each cell */}
            {columns.map((col, colIndex) => (
                <EditableCell
                    key={col.id || colIndex} // Use column ID as part of key
                    // Pass cell value from the row's cells array based on column index
                    initialValue={row.cells?.[colIndex] ?? ''} // Use nullish coalescing for default
                    isEditing={isEditing}
                    onSave={(newValue) => onCellChange(rowIndex, colIndex, newValue)}
                    rowIndex={rowIndex}
                    colIndex={colIndex}
                />
            ))}

             {/* Delete Row Cell (Conditional) - Renders only if isEditing is true, sticky right */}
             {isEditing && (
                <td className="delete-cell table-cell-bordered text-center align-middle p-1 bg-background sticky right-0 z-10">
                    <Button
                         variant="danger"
                         size="sm"
                         className="w-6 h-6 p-0 leading-none rounded-full opacity-70 group-hover:opacity-100 transition-opacity" // Show on row hover
                         title={`Delete row ${row.order}`}
                         onClick={() => onDeleteRow(row.id)} // Pass row ID to delete handler
                         aria-label={`Delete row ${row.order}`}
                         disabled={!row.id} // Disable delete for newly added (unsaved) rows if ID is null
                     >
                        &times; {/* Simple 'X' icon */}
                    </Button>
                </td>
             )}
        </tr>
    );
});


// Main DataTable Component
function DataTable({
    columns = [], // Array of column objects { id, name, order, width }
    rows = [],    // Array of row objects { id, order, cells: [...], status?: '...' }
    isEditing = false,       // Is the table in edit mode?
    isTodoTable = false,     // Does the table represent a ToDo list?
    onCellChange = () => {}, // Callback for cell edits: (rowIndex, colIndex, newValue) => void
    onDeleteRow = () => {},  // Callback for row deletion: (rowId) => void
    onAddColumn = () => {},  // Callback to add a new column
    onDeleteColumn = () => {},// Callback to delete a column: (columnId) => void
    onColumnResize = () => {},// Callback for column resize: (columnId, newWidth) => void
    onStatusChange = () => {}, // Callback for ToDo status change: (rowId, newStatus) => void
}) {

    // Memoize columns and rows to potentially optimize re-renders, though rows might change often in edit mode.
    const memoizedColumns = useMemo(() => columns, [columns]);
    const memoizedRows = useMemo(() => rows, [rows]);

    // Calculate total number of columns for potential layout adjustments (e.g., spanning add row button)
    const totalRenderedColumns = 1 + (isTodoTable ? 1 : 0) + memoizedColumns.length + (isEditing ? 1 : 0);

    return (
        // Wrapper div for horizontal scrolling if table content overflows
        <div className="overflow-x-auto border border-table-border rounded shadow-sm relative"> {/* Added relative for sticky positioning context */}
            <table id="data-table" className="w-full border-collapse table-auto text-sm"> {/* Use table-auto for column width flexibility initially */}
                {/* Define column groups for width control */}
                <colgroup>
                    {/* Row Number Column */}
                    <col style={{ width: '40px', minWidth: '40px' }} />
                    {/* Status Column (if ToDo) */}
                    {isTodoTable && <col style={{ width: '140px', minWidth: '120px' }} />}
                    {/* Data Columns - Use defined width or default */}
                    {memoizedColumns.map((col) => (
                        <col key={col.id || col.order} style={{ width: `${col.width || 150}px`, minWidth: '80px' }} />
                    ))}
                    {/* Delete/Add Column (only in edit mode) */}
                    {isEditing && <col style={{ width: '50px', minWidth: '50px' }} />}
                </colgroup>
                {/* Table Header */}
                <thead className="sticky top-0 z-20 bg-background"> {/* Make header sticky */}
                    <tr className='border-b border-table-border'>
                        {/* Row Number Header - Sticky Left */}
                        <th className="table-cell-bordered p-2 text-center bg-background text-font-color font-semibold sticky left-0 z-10 text-xs">#</th>

                        {/* Status Header (if ToDo) */}
                        {isTodoTable && (
                             <th className="table-cell-bordered p-2 text-left bg-background text-font-color font-semibold">Status</th>
                        )}

                        {/* Data Column Headers */}
                        {memoizedColumns.map((col) => (
                            <th key={col.id || col.order} className="dynamic-column table-cell-bordered px-2 py-1.5 text-left bg-background text-font-color font-semibold group relative whitespace-nowrap">
                                <div className="flex justify-between items-center h-full">
                                     {/* Column Name */}
                                     <span className="truncate pr-2 py-0.5">{col.name}</span>
                                     {/* Column Actions (Delete) - Appears on hover when editing */}
                                     {isEditing && (
                                         <button
                                             className="delete-column opacity-0 group-hover:opacity-100 transition-opacity absolute right-1 top-1/2 transform -translate-y-1/2 w-4 h-4 leading-none flex items-center justify-center bg-red-500 text-white border-none rounded-full cursor-pointer text-xs p-0 hover:bg-red-700 focus:outline-none focus:ring-1 focus:ring-red-600"
                                             title={`Delete column "${col.name}"`}
                                             onClick={(e) => { e.stopPropagation(); onDeleteColumn(col.id); }} // Prevent triggering potential sort/resize
                                             aria-label={`Delete column ${col.name}`}
                                         >
                                             &times;
                                         </button>
                                     )}
                                     {/* TODO: Add Resizing Handle Element */}
                                     {/* <div className="resize-handle absolute right-0 top-0 bottom-0 w-1 cursor-col-resize"></div> */}
                                </div>
                            </th>
                        ))}

                        {/* Add Column / Delete Header - Sticky Right */}
                        {isEditing && (
                             <th className="table-cell-bordered p-1 text-center bg-background text-font-color sticky right-0 z-10">
                                 {/* Add Column Button */}
                                 <button
                                     onClick={onAddColumn}
                                     className="w-6 h-6 leading-none bg-green-500 text-white rounded-full text-lg font-bold hover:bg-green-600 focus:outline-none focus:ring-1 focus:ring-green-600 transition-colors"
                                     title="Add new column"
                                     aria-label="Add new column"
                                 >+</button>
                                 {/* This header could also signify the delete row column below */}
                             </th>
                        )}
                    </tr>
                </thead>
                {/* Table Body */}
                <tbody>
                    {/* Render memoized rows */}
                    {memoizedRows.map((row, rowIndex) => (
                         <MemoizedRow
                             key={row.id || rowIndex} // Use row ID if available for stable key
                             row={row}
                             columns={memoizedColumns}
                             isEditing={isEditing}
                             isTodoTable={isTodoTable}
                             rowIndex={rowIndex}
                             onCellChange={onCellChange}
                             onDeleteRow={onDeleteRow}
                             onStatusChange={onStatusChange} // Pass status handler down
                         />
                    ))}
                     {/* Handle empty state within the table body */}
                     {memoizedRows.length === 0 && (
                         <tr>
                             <td colSpan={totalRenderedColumns} className="text-center py-4 text-gray-500 italic table-cell-bordered">
                                 This table is empty. {isEditing ? "Add a row to get started." : ""}
                             </td>
                         </tr>
                     )}
                </tbody>
            </table>
        </div>
    );
}

export default DataTable;