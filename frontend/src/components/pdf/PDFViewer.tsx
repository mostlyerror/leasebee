'use client';

import { useState, useRef, useCallback, useEffect, forwardRef, useImperativeHandle } from 'react';
import { Document, Page, pdfjs } from 'react-pdf';
import 'react-pdf/dist/esm/Page/AnnotationLayer.css';
import 'react-pdf/dist/esm/Page/TextLayer.css';
import { ConfidenceHeatmap, HeatmapLegend } from './ConfidenceHeatmap';
import { FileX, RefreshCw } from 'lucide-react';

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

export interface PDFViewerRef {
  scrollToPage: (page: number) => void;
  scrollToField: (page: number, boundingBox?: BoundingBox) => void;
}

export const PDFViewer = forwardRef<PDFViewerRef, PDFViewerProps>(function PDFViewer(
  { url, heatmapFields = [], activeField, onFieldClick, onPageClick },
  ref
) {
  const [numPages, setNumPages] = useState<number>(0);
  const [pageNumber, setPageNumber] = useState<number>(1);
  const [scale, setScale] = useState<number>(1.2);
  const [heatmapVisible, setHeatmapVisible] = useState<boolean>(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const pageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  // Reset error when URL changes
  useEffect(() => {
    setLoadError(null);
  }, [url]);

  // When react-pdf fails, fetch the URL again to get the server error message
  const handleLoadError = useCallback(() => {
    if (loadError) return;
    fetch(url).then((res) => {
      if (!res.ok) {
        res.json().catch(() => null).then((body) => {
          const detail = body?.detail || `Server returned ${res.status}`;
          if (res.status === 404 || detail.includes('not found')) {
            setLoadError('Lease not found. It may have been deleted.');
          } else if (detail.includes('No such file')) {
            setLoadError('The PDF file is no longer available. It may need to be re-uploaded.');
          } else {
            setLoadError(detail);
          }
        });
      } else {
        setLoadError('Failed to load PDF. The file may be corrupted.');
      }
    }).catch(() => {
      setLoadError('Unable to reach the server. Is the backend running?');
    });
  }, [url, loadError]);

  const onDocumentLoadSuccess = useCallback(({ numPages }: { numPages: number }) => {
    setLoadError(null);
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

  // Expose scroll methods to parent via ref
  useImperativeHandle(ref, () => ({
    scrollToPage,
    scrollToField,
  }), [scrollToPage, scrollToField]);

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

        {/* Heatmap Legend */}
        <div className="flex-shrink-0">
          <HeatmapLegend
            onToggle={() => setHeatmapVisible(!heatmapVisible)}
            isVisible={heatmapVisible}
          />
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
        {loadError ? (
          <div className="flex flex-col items-center justify-center h-96 text-center px-6">
            <div className="w-14 h-14 bg-red-100 rounded-full flex items-center justify-center mb-4">
              <FileX className="w-7 h-7 text-red-500" />
            </div>
            <p className="text-sm font-medium text-slate-900 mb-1">PDF unavailable</p>
            <p className="text-sm text-slate-500 max-w-sm mb-4">{loadError}</p>
            <button
              onClick={() => { setLoadError(null); setNumPages(0); }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry
            </button>
          </div>
        ) : (
        <Document
          file={url}
          onLoadSuccess={onDocumentLoadSuccess}
          onLoadError={handleLoadError}
          loading={
            <div className="flex items-center justify-center h-96">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
            </div>
          }
          error={<></>}
        >
          {Array.from(new Array(numPages), (_, index) => {
            const page = index + 1;
            const pageFields = getFieldsForPage(page);
            const isActivePage = activeField && pageFields.some(f => f.fieldPath === activeField);

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

                {/* Confidence Heatmap Overlays */}
                {heatmapVisible && (
                  <ConfidenceHeatmap
                    fields={pageFields}
                    activeField={activeField || null}
                    onFieldClick={onFieldClick || (() => {})}
                    scale={scale}
                  />
                )}
              </div>
            );
          })}
        </Document>
        )}
      </div>
    </div>
  );
});
