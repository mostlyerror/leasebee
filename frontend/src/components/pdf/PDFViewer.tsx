'use client';

import { useState, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';

// Set PDF.js worker
if (typeof window !== 'undefined') {
  pdfjs.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjs.version}/pdf.worker.min.js`;
}

interface BoundingBox {
  x0: number;
  y0: number;
  x1: number;
  y1: number;
}

interface Highlight {
  fieldPath: string;
  page: number;
  boundingBox?: BoundingBox;
  color: string;
}

interface PDFViewerProps {
  url: string;
  highlights?: Highlight[];
  activeField?: string | null;
  onPageClick?: (page: number, x: number, y: number) => void;
}

export function PDFViewer({ url, highlights = [], activeField, onPageClick }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.2);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  }, []);

  // Scroll to specific page when activeField changes
  const scrollToPage = useCallback((page: number) => {
    const pageElement = pageRefs.current.get(page);
    if (pageElement && containerRef.current) {
      pageElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      setPageNumber(page);
    }
  }, []);

  // Expose scrollToPage to parent
  if (typeof window !== 'undefined') {
    (window as any).pdfScrollToPage = scrollToPage;
  }

  const goToPrevPage = () => setPageNumber((prev) => Math.max(prev - 1, 1));
  const goToNextPage = () => setPageNumber((prev) => Math.min(prev + 1, numPages));
  const zoomIn = () => setScale((prev) => Math.min(prev + 0.2, 3));
  const zoomOut = () => setScale((prev) => Math.max(prev - 0.2, 0.5));

  // Get highlights for current page
  const getHighlightsForPage = (page: number) => {
    return highlights.filter((h) => h.page === page);
  };

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b">
        <div className="flex items-center gap-2">
          <button
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
            className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            ← Prev
          </button>
          <span className="text-sm">
            Page {pageNumber} of {numPages}
          </span>
          <button
            onClick={goToNextPage}
            disabled={pageNumber >= numPages}
            className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200 disabled:opacity-50"
          >
            Next →
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={zoomOut}
            className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
          >
            −
          </button>
          <span className="text-sm">{Math.round(scale * 100)}%</span>
          <button
            onClick={zoomIn}
            className="px-3 py-1 text-sm bg-gray-100 rounded hover:bg-gray-200"
          >
            +
          </button>
        </div>
      </div>

      {/* PDF Container */}
      <div
        ref={containerRef}
        className="flex-1 overflow-auto p-4"
      >
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          loading={
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          }
          error={
            <div className="text-red-500 text-center py-8">
              Failed to load PDF
            </div>
          }
        >
          {Array.from(new Array(numPages), (_, index) => {
            const page = index + 1;
            const pageHighlights = getHighlightsForPage(page);
            const isActivePage = activeField && pageHighlights.some(h => h.fieldPath === activeField);

            return (
              <div
                key={`page_${page}`}
                ref={(el) => {
                  if (el) pageRefs.current.set(page, el);
                }}
                className={`mb-4 relative ${isActivePage ? 'ring-4 ring-blue-400 rounded' : ''}`}
              >
                <Page
                  pageNumber={page}
                  scale={scale}
                  renderTextLayer={true}
                  renderAnnotationLayer={false}
                  className="shadow-lg"
                />
                
                {/* Highlight overlays */}
                {pageHighlights.map((highlight, idx) => (
                  <div
                    key={`${highlight.fieldPath}_${idx}`}
                    className={`absolute pointer-events-none transition-all duration-300 ${
                      highlight.fieldPath === activeField
                        ? 'bg-yellow-300 opacity-60 animate-pulse'
                        : 'bg-yellow-200 opacity-40'
                    }`}
                    style={{
                      left: `${(highlight.boundingBox?.x0 || 0) * scale}px`,
                      top: `${(highlight.boundingBox?.y0 || 0) * scale}px`,
                      width: `${((highlight.boundingBox?.x1 || 100) - (highlight.boundingBox?.x0 || 0)) * scale}px`,
                      height: `${((highlight.boundingBox?.y1 || 20) - (highlight.boundingBox?.y0 || 0)) * scale}px`,
                    }}
                  />
                ))}
              </div>
            );
          })}
        </Document>
      </div>
    </div>
  );
}
