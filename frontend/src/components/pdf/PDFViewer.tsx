'use client';

import { useState, useRef, useCallback } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import { ConfidenceHeatmap, HeatmapLegend } from './ConfidenceHeatmap';

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

interface HeatmapField {
  fieldPath: string;
  label: string;
  page: number;
  confidence: number;
  boundingBox?: BoundingBox;
}

interface PDFViewerProps {
  url: string;
  heatmapFields?: HeatmapField[];
  activeField?: string | null;
  onFieldClick?: (fieldPath: string) => void;
  onPageClick?: (page: number, x: number, y: number) => void;
}

export function PDFViewer({ url, heatmapFields = [], activeField, onFieldClick, onPageClick }: PDFViewerProps) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.2);
  const [heatmapVisible, setHeatmapVisible] = useState<boolean>(true);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
  }, []);

  // Scroll to specific page when activeField changes
  const scrollToPage = useCallback((page: number) => {
    const pageElement = pageRefs.current.get(page);
    if (pageElement && containerRef.current) {
      pageElement.scrollIntoView({ behavior: 'auto', block: 'center' });
      setPageNumber(page);
    }
  }, []);

  // Scroll to specific field with bounding box, centering it in viewport
  const scrollToField = useCallback((page: number, boundingBox?: BoundingBox) => {
    const pageElement = pageRefs.current.get(page);
    const container = containerRef.current;

    if (!pageElement || !container) return;

    // If no bounding box, just scroll to page
    if (!boundingBox) {
      scrollToPage(page);
      return;
    }

    // Calculate the center of the bounding box
    const centerY = ((boundingBox.y0 + boundingBox.y1) / 2) * scale;

    // Get the page's offset relative to the container
    const pageRect = pageElement.getBoundingClientRect();
    const containerRect = container.getBoundingClientRect();

    // Calculate scroll position to center the bounding box
    const pageOffsetInContainer = pageElement.offsetTop;
    const targetScrollTop = pageOffsetInContainer + centerY - (containerRect.height / 2);

    // Scroll instantly to center the field
    container.scrollTo({
      top: targetScrollTop,
      behavior: 'auto'
    });

    setPageNumber(page);
  }, [scale, scrollToPage]);

  // Expose scroll methods to parent
  if (typeof window !== 'undefined') {
    (window as any).pdfScrollToPage = scrollToPage;
    (window as any).pdfScrollToField = scrollToField;
  }

  const goToPrevPage = () => {
    const newPage = Math.max(pageNumber - 1, 1);
    setPageNumber(newPage);
    scrollToPage(newPage);
  };

  const goToNextPage = () => {
    const newPage = Math.min(pageNumber + 1, numPages);
    setPageNumber(newPage);
    scrollToPage(newPage);
  };
  const zoomIn = () => setScale((prev) => Math.min(prev + 0.2, 3));
  const zoomOut = () => setScale((prev) => Math.max(prev - 0.2, 0.5));

  // Get heatmap fields for current page
  const getFieldsForPage = (page: number) => {
    return heatmapFields.filter((f) => f.page === page);
  };

  return (
    <div className="flex flex-col h-full bg-gray-100">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 bg-white border-b gap-4">
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

        {/* Spacer */}
        <div className="flex-1"></div>

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

            return (
              <div
                key={`page_${page}`}
                ref={(el) => {
                  if (el) pageRefs.current.set(page, el);
                }}
                className="mb-4 relative"
              >
                <Page
                  pageNumber={page}
                  scale={scale}
                  renderTextLayer={true}
                  renderAnnotationLayer={false}
                  className="shadow-lg"
                />
              </div>
            );
          })}
        </Document>
      </div>
    </div>
  );
}
