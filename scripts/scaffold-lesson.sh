#!/bin/bash
# Helper script to scaffold a new lesson directory structure

set -e

if [ $# -lt 1 ]; then
    echo "Usage: $0 <lesson-number> [lesson-title]"
    echo "Example: $0 02 'Ethical Agents & BDI Systems'"
    exit 1
fi

LESSON_NUM=$1
LESSON_TITLE=${2:-"Lesson $LESSON_NUM"}
LESSON_DIR=$(printf "lesson-%02d" $LESSON_NUM)

if [ -d "$LESSON_DIR" ]; then
    echo "Error: $LESSON_DIR already exists"
    exit 1
fi

echo "Scaffolding $LESSON_DIR..."

# Create directory structure
mkdir -p "$LESSON_DIR"/{scripts,slides,examples}

# Copy docker-compose.yml from lesson-01
cp lesson-01/docker-compose.yml "$LESSON_DIR/"
# Update service name
sed -i "s/computational-ethics-lesson-01/computational-ethics-${LESSON_DIR}/g" "$LESSON_DIR/docker-compose.yml"

# Copy scripts
cp lesson-01/scripts/*.sh "$LESSON_DIR/scripts/"
chmod +x "$LESSON_DIR/scripts/"*.sh

# Create slides/main.tex from template
cat > "$LESSON_DIR/slides/main.tex" << 'EOF'
\documentclass{beamer}

\usetheme{AMS}
\usecolortheme{AMSBolognaFC}

\usepackage[english]{babel}
\usepackage[utf8]{inputenc}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{listings}
\usepackage{xcolor}

\title{LESSON_TITLE}
\subtitle{Computational Ethics 2026}
\author{}
\date{\today}

\begin{document}

\frame{\titlepage}

\begin{frame}{Overview}
  \begin{itemize}
    \item TODO: Add content
  \end{itemize}
\end{frame}

\end{document}
EOF

# Replace placeholder
sed -i "s/LESSON_TITLE/$LESSON_TITLE/g" "$LESSON_DIR/slides/main.tex"

# Copy LaTeX support files from lesson-01
cp lesson-01/slides/*.sty "$LESSON_DIR/slides/" 2>/dev/null || true
cp lesson-01/slides/*.bst "$LESSON_DIR/slides/" 2>/dev/null || true
cp lesson-01/slides/references.bib "$LESSON_DIR/slides/" 2>/dev/null || true

# Create example file marker
cat > "$LESSON_DIR/examples/README.md" << EOF
# Lesson $LESSON_NUM Examples

Add example files here.

## Running Examples

\`\`\`bash
./scripts/run-clingo.sh examples/01-example.lp
\`\`\`
EOF

# Create README
cat > "$LESSON_DIR/README.md" << EOF
# Lesson $LESSON_NUM - $LESSON_TITLE

## Quick Start

### Build Slides
\`\`\`bash
cd $LESSON_DIR
./scripts/build-slides.sh
\`\`\`

### Run Examples
\`\`\`bash
./scripts/run-clingo.sh examples/01-example.lp
\`\`\`

### Clean Build
\`\`\`bash
./scripts/build-slides.sh --clean
\`\`\`

## Structure

- \`slides/\` - LaTeX presentation files
- \`examples/\` - Example code files
- \`scripts/\` - Helper scripts for building and running code
EOF

echo ""
echo "✓ Successfully scaffolded $LESSON_DIR"
echo ""
echo "Next steps:"
echo "1. Edit $LESSON_DIR/slides/main.tex with your content"
echo "2. Add example files to $LESSON_DIR/examples/"
echo "3. Test with: ./$LESSON_DIR/scripts/build-slides.sh"
echo ""
echo "When ready to release:"
echo "  git add $LESSON_DIR/"
echo "  git commit -m 'Add lesson-$LESSON_NUM'"
echo "  git tag lesson-$(printf '%02d' $LESSON_NUM)-v1.0.0"
echo "  git push --tags"
