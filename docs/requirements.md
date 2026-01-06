# Requirements

Product requirements and functional specifications for the AI File Search system.

## Product Vision

A zero-configuration smart document search system with automatic discovery and real-time indexing, enabling users to search their local documents using natural language and receive AI-powered answers with citations.

## Core Requirements

### FR-001: Document Processing
| ID | Requirement | Status |
|----|-------------|--------|
| FR-001.1 | Support PDF file extraction | Done |
| FR-001.2 | Support DOCX file extraction | Done |
| FR-001.3 | Support TXT file processing | Done |
| FR-001.4 | Support Markdown file processing | Done |

### FR-002: Semantic Search
| ID | Requirement | Status |
|----|-------------|--------|
| FR-002.1 | Index documents using sentence embeddings | Done |
| FR-002.2 | Search using natural language queries | Done |
| FR-002.3 | Return relevance-ranked results | Done |
| FR-002.4 | Filter irrelevant queries (threshold 1.2) | Done |

### FR-003: AI Answer Generation
| ID | Requirement | Status |
|----|-------------|--------|
| FR-003.1 | Generate answers from retrieved context | Done |
| FR-003.2 | Include citations to source documents | Done |
| FR-003.3 | Stream responses in real-time | Done |
| FR-003.4 | Support CPU-only inference | Done |
| FR-003.5 | Optimize context processing for <60s first token | Done |

### FR-004: File Watching
| ID | Requirement | Status |
|----|-------------|--------|
| FR-004.1 | Detect file changes in real-time | Done |
| FR-004.2 | Debounce rapid changes (5s default) | Done |
| FR-004.3 | Schedule nightly reindexing (2:00 AM) | Done |
| FR-004.4 | Run as background daemon | Done |

### FR-005: User Interface
| ID | Requirement | Status |
|----|-------------|--------|
| FR-005.1 | Command-line interface for queries | Done |
| FR-005.2 | Web UI with Flask | Done |
| FR-005.6 | Display citations with file references | Done |
| FR-005.7 | Interactive citations with Open buttons | Done |
| FR-005.8 | Show performance metrics | Done |
| FR-005.5 | Standalone Desktop App (PyWebview) | Pending |
| FR-005.6 | Live Activity Log Viewer | Done |

### FR-006: Multi-Folder Watching
| ID | Requirement | Status |
|----|-------------|--------|
| FR-006.1 | Watch multiple disjoint folders | Done |
| FR-006.2 | Configure watch paths via UI | Done |
| FR-006.3 | Validate paths (security check) | Done |
| FR-006.4 | Remove intermediate extracts folder | Done |

### FR-007: Future Enhancements
| ID | Requirement | Status |
|----|-------------|--------|
| FR-007.1 | Standalone Desktop App (PyWebview) | Pending |
| FR-007.2 | Unified Launcher (Auto-start watcher) | Pending |
| FR-007.3 | Embedded System Status Panel | Pending |

### FR-009: Confluence Integration
| ID | Requirement | Status |
|----|-------------|--------|
| FR-009.1 | Connect to Confluence Cloud via API | Done |
| FR-009.2 | Fetch pages from Confluence space | Done |
| FR-009.3 | Parse Confluence HTML and macros to plain text | Done |
| FR-009.4 | Preserve folder hierarchy in metadata | Done |
| FR-009.5 | Support incremental sync (only changed pages) | Done |
| FR-009.6 | CLI command for Confluence sync | Done |
| FR-009.7 | UI settings panel for Confluence | Done |
| FR-009.8 | Index Confluence attachments (PDF, DOCX) | Pending |

### FR-008: Developer Tools
| ID | Requirement | Status |
|----|-------------|--------|
| FR-008.1 | Sync copilot-instructions.md across repos | Done |
| FR-008.2 | Auto-detect source file in current repo | Done |
| FR-008.3 | Configure .git/info/exclude automatically | Done |
| FR-008.4 | Verify git exclusion with status check | Done |
| FR-008.5 | Find highest version across all repos | Done |
| FR-008.6 | Reverse sync from targets if newer | Done |
| FR-008.7 | Session startup sync reminder | Done |
| FR-008.8 | Model benchmark tool for speed/quality comparison | Done |

### FR-010: Team Distribution
| ID | Requirement | Status |
|----|-------------|--------|
| FR-010.1 | Cross-platform installer scripts (Windows/macOS/Linux) | Done |
| FR-010.2 | One-click launcher scripts | Done |
| FR-010.3 | Automatic AI model download from Hugging Face | Done |
| FR-010.4 | Desktop shortcut creation | Done |
| FR-010.5 | Team installation guide | Done |
| FR-010.6 | Remove legacy Phi-3.5 model (use Qwen2.5 only) | Done |

### FR-011: Version Checker & Distribution Automation
| ID | Requirement | Status |
|----|-------------|--------|
| FR-011.1 | VERSION file as single source of truth | Done |
| FR-011.2 | Version management module (core/version.py) | Done |
| FR-011.3 | API endpoint for version info (/api/version) | Done |
| FR-011.4 | Update notification banner in UI | Done |
| FR-011.5 | Non-blocking async update check on startup | Done |
| FR-011.6 | ZIP build script with proper exclusions | Done |
| FR-011.7 | latest_version.txt for cloud hosting | Done |
| FR-011.8 | Google Drive distribution support | Done |

## Non-Functional Requirements

### NFR-001: Performance
| ID | Requirement | Target | Achieved |
|----|-------------|--------|----------|
| NFR-001.1 | Index build time | < 60s | 40.34s |
| NFR-001.2 | Query response time | < 200ms | 17.4ms |
| NFR-001.3 | Answer generation time | < 60s | 19s (with Qwen2.5, improved from 63s with Phi-3.5) |

### NFR-002: Resource Usage
| ID | Requirement | Target |
|----|-------------|--------|
| NFR-002.1 | Memory usage | < 4GB |
| NFR-002.2 | Storage for models | < 3GB |
| NFR-002.3 | CPU threads | Configurable (default 8) |

### NFR-003: Compatibility
| ID | Requirement | Status |
|----|-------------|--------|
| NFR-003.1 | Windows support | Done |
| NFR-003.2 | macOS support | Done |
| NFR-003.3 | Linux support | Done |
| NFR-003.4 | Python 3.12+ | Required |

## External References

- Original PRD: [PRD_v0.4.docx](PRD_v0.4.docx)

---

*Last Updated: 2025-12-25*
