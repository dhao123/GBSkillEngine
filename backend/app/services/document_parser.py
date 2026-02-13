"""
GBSkillEngine 文档解析服务

支持PDF和DOCX文档的文本提取
"""
import os
import re
import logging
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ParsedDocument:
    """解析后的文档结构"""
    text: str  # 全文文本
    title: str = ""  # 文档标题
    sections: List[Dict[str, Any]] = field(default_factory=list)  # 章节结构
    tables: List[Dict[str, Any]] = field(default_factory=list)  # 表格数据
    metadata: Dict[str, Any] = field(default_factory=dict)  # 元数据


class DocumentParser:
    """文档解析器"""
    
    def __init__(self):
        self._fitz = None  # PyMuPDF
        self._docx = None  # python-docx
    
    def _get_fitz(self):
        """延迟加载PyMuPDF"""
        if self._fitz is None:
            try:
                import fitz
                self._fitz = fitz
            except ImportError:
                logger.warning("PyMuPDF未安装，PDF解析将不可用")
                raise ImportError("PyMuPDF未安装，请安装: pip install PyMuPDF")
        return self._fitz
    
    def _get_docx(self):
        """延迟加载python-docx"""
        if self._docx is None:
            try:
                import docx
                self._docx = docx
            except ImportError:
                logger.warning("python-docx未安装，DOCX解析将不可用")
                raise ImportError("python-docx未安装，请安装: pip install python-docx")
        return self._docx
    
    def parse(self, file_path: str) -> ParsedDocument:
        """
        解析文档
        
        Args:
            file_path: 文档文件路径
            
        Returns:
            ParsedDocument: 解析结果
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文档文件不存在: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            return self._parse_pdf(file_path)
        elif ext in [".doc", ".docx"]:
            return self._parse_docx(file_path)
        else:
            raise ValueError(f"不支持的文件格式: {ext}")
    
    def _parse_pdf(self, file_path: str) -> ParsedDocument:
        """解析PDF文档"""
        fitz = self._get_fitz()
        
        text_parts = []
        tables = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num, page in enumerate(doc):
                # 提取文本
                page_text = page.get_text("text")
                text_parts.append(page_text)
                
                # 尝试提取表格（基于文本布局分析）
                page_tables = self._extract_tables_from_text(page_text, page_num + 1)
                tables.extend(page_tables)
            
            doc.close()
            
            full_text = "\n".join(text_parts)
            
            # 提取标题（通常是第一行或前几行）
            title = self._extract_title(full_text)
            
            # 提取章节结构
            sections = self._extract_sections(full_text)
            
            return ParsedDocument(
                text=full_text,
                title=title,
                sections=sections,
                tables=tables,
                metadata={"file_type": "pdf", "page_count": len(text_parts)}
            )
            
        except Exception as e:
            logger.error(f"PDF解析失败: {str(e)}")
            raise RuntimeError(f"PDF解析失败: {str(e)}")
    
    def _parse_docx(self, file_path: str) -> ParsedDocument:
        """解析DOCX文档"""
        docx = self._get_docx()
        
        text_parts = []
        tables = []
        
        try:
            doc = docx.Document(file_path)
            
            # 提取段落文本
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)
            
            # 提取表格
            for table_idx, table in enumerate(doc.tables):
                table_data = self._extract_docx_table(table, table_idx + 1)
                if table_data:
                    tables.append(table_data)
            
            full_text = "\n".join(text_parts)
            
            # 提取标题
            title = self._extract_title(full_text)
            
            # 提取章节结构
            sections = self._extract_sections(full_text)
            
            return ParsedDocument(
                text=full_text,
                title=title,
                sections=sections,
                tables=tables,
                metadata={"file_type": "docx", "paragraph_count": len(text_parts)}
            )
            
        except Exception as e:
            logger.error(f"DOCX解析失败: {str(e)}")
            raise RuntimeError(f"DOCX解析失败: {str(e)}")
    
    def _extract_docx_table(self, table, table_idx: int) -> Optional[Dict[str, Any]]:
        """从DOCX提取表格数据"""
        try:
            rows = []
            headers = []
            
            for row_idx, row in enumerate(table.rows):
                row_data = [cell.text.strip() for cell in row.cells]
                
                if row_idx == 0:
                    headers = row_data
                else:
                    rows.append(row_data)
            
            if not headers and not rows:
                return None
            
            return {
                "table_id": f"table_{table_idx}",
                "headers": headers,
                "rows": rows,
                "row_count": len(rows),
                "col_count": len(headers) if headers else (len(rows[0]) if rows else 0)
            }
        except Exception as e:
            logger.warning(f"表格提取失败: {str(e)}")
            return None
    
    def _extract_tables_from_text(self, text: str, page_num: int) -> List[Dict[str, Any]]:
        """从文本中提取表格（基于布局分析）"""
        tables = []
        
        # 查找表格标记（如"表1"、"表 2"等）
        table_pattern = r"表\s*(\d+)[：:\s]*([\u4e00-\u9fa5a-zA-Z0-9\s]+)"
        matches = re.finditer(table_pattern, text)
        
        for match in matches:
            table_num = match.group(1)
            table_title = match.group(2).strip()
            
            tables.append({
                "table_id": f"table_{table_num}",
                "title": table_title,
                "page": page_num,
                "raw_position": match.start()
            })
        
        return tables
    
    def _extract_title(self, text: str) -> str:
        """提取文档标题"""
        lines = text.strip().split("\n")
        
        for line in lines[:10]:  # 检查前10行
            line = line.strip()
            # 标题通常包含"GB"或是较长的中文描述
            if line and (
                "GB" in line.upper() or 
                re.match(r"^[\u4e00-\u9fa5]{4,}", line)
            ):
                return line[:100]  # 限制长度
        
        return lines[0][:100] if lines else ""
    
    def _extract_sections(self, text: str) -> List[Dict[str, Any]]:
        """提取章节结构"""
        sections = []
        
        # 匹配章节标题模式（如"1 范围"、"4.2 技术要求"等）
        section_pattern = r"^(\d+(?:\.\d+)*)\s+([\u4e00-\u9fa5a-zA-Z\s]+)"
        
        for line in text.split("\n"):
            line = line.strip()
            match = re.match(section_pattern, line)
            if match:
                section_num = match.group(1)
                section_title = match.group(2).strip()
                
                # 确定层级
                level = section_num.count(".") + 1
                
                sections.append({
                    "number": section_num,
                    "title": section_title,
                    "level": level
                })
        
        return sections
    
    def extract_dimension_tables(self, parsed_doc: ParsedDocument) -> Dict[str, Any]:
        """
        从解析后的文档中提取尺寸规格表
        
        专门用于提取管材类国标中的DN-外径-壁厚对应表
        """
        dimension_tables = {}
        
        # 查找DN相关表格
        dn_pattern = r"DN\s*(\d+)"
        od_pattern = r"外径[^0-9]*(\d+(?:\.\d+)?)"
        pn_pattern = r"PN\s*(\d+(?:\.\d+)?)"
        
        # 从表格中提取
        for table in parsed_doc.tables:
            headers = table.get("headers", [])
            rows = table.get("rows", [])
            
            # 检测是否是尺寸表
            header_text = " ".join(headers).lower()
            if any(kw in header_text for kw in ["dn", "外径", "壁厚", "公称"]):
                dimension_tables[table.get("table_id", "unknown")] = {
                    "headers": headers,
                    "data": rows,
                    "type": "dimension"
                }
        
        return dimension_tables


# 全局解析器实例
document_parser = DocumentParser()


def parse_standard_document(file_path: str) -> ParsedDocument:
    """
    解析国标文档
    
    Args:
        file_path: 文档路径
        
    Returns:
        ParsedDocument: 解析结果
    """
    return document_parser.parse(file_path)
