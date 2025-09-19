# backend/reporting.py
import io
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
import pandas as pd
import matplotlib.pyplot as plt

def generate_pdf_report(df: pd.DataFrame):
    """
    Generates a PDF report from the results DataFrame.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    
    elements = []

    # Title
    elements.append(Paragraph("Heavy Metal Pollution Index (HMPI) Analysis Report", styles['h1']))
    elements.append(Spacer(1, 0.25*inch))

    # Summary Stats
    num_samples = len(df)
    polluted_samples = len(df[df['HMPI'] >= 100])
    summary_text = f"<b>Total Samples Analyzed:</b> {num_samples}<br/>"
    summary_text += f"<b>Samples with HMPI ≥ 100 (Polluted):</b> {polluted_samples} ({polluted_samples/num_samples:.1%})"
    elements.append(Paragraph(summary_text, styles['bodytext']))
    elements.append(Spacer(1, 0.25*inch))
    
    # Chart
    try:
        fig_buffer = io.BytesIO()
        category_counts = df['HMPI_Category'].value_counts()
        plt.figure(figsize=(6, 4))
        category_counts.plot(kind='bar', color=['darkred', 'red', 'orange', 'green'])
        plt.title('Distribution of HMPI Categories')
        plt.ylabel('Number of Samples')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(fig_buffer, format='png')
        plt.close()
        fig_buffer.seek(0)
        
        img = Image(fig_buffer, width=5*inch, height=3*inch)
        elements.append(img)
        elements.append(Spacer(1, 0.25*inch))
    except Exception as e:
        elements.append(Paragraph(f"Could not generate chart: {e}", styles['bodytext']))

    # Results Table
    elements.append(Paragraph("Results Summary", styles['h2']))
    # Select key columns and limit rows for PDF readability
    cols_to_show = ['SampleID', 'HMPI', 'HMPI_Category', 'MCI', 'MCI_Category']
    display_df = df[cols_to_show].head(30) # Show first 30 samples in PDF
    
    table_data = [display_df.columns.tolist()] + display_df.values.tolist()
    t = Table(table_data, colWidths=[1.5*inch, 1.2*inch, 1.8*inch, 1.2*inch, 2.0*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    
    doc.build(elements)
    buffer.seek(0)
    return buffer