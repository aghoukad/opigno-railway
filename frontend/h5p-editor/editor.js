/**
 * H5P CKEditor integration derived from h5p/h5p-editor-php-library.
 * CKEditor 5 is distributed under GPL-2.0-or-later; this build uses GPL-3.0-or-later.
 */
import { ClassicEditor, Plugin, Alignment, AutoLink, Autoformat, BlockQuote, Bold, Code, CodeBlock, Essentials, FontBackgroundColor, FontColor, FontFamily, FontSize, GeneralHtmlSupport, Heading, Highlight, HorizontalLine, Image, ImageCaption, ImageStyle, ImageToolbar, ImageUpload, Indent, IndentBlock, Italic, Link, List, MediaEmbed, Paragraph, PasteFromOffice, RemoveFormat, SelectAll, Strikethrough, Subscript, Superscript, Table, TableCaption, TableCellProperties, TableColumnResize, TableProperties, TableToolbar, TextTransformation, Underline } from 'ckeditor5';
import css from 'ckeditor5/ckeditor5.css';

const style = document.createElement('style');
style.setAttribute('data-cke', 'true');
style.textContent = css;
document.head.appendChild(style);

class NonBreakingSpace extends Plugin {
  static get pluginName() { return 'NonBreakingSpace'; }
  init() {
    this.editor.keystrokes.set('CTRL+SHIFT+SPACE', (data, cancel) => {
      cancel();
      this.editor.model.change(writer => {
        this.editor.model.insertContent(writer.createText('\u00A0'));
      });
    });
  }
}

class H5PEditor extends ClassicEditor {
  static builtinPlugins = [Alignment, AutoLink, Autoformat, BlockQuote, Bold, Code, CodeBlock, Essentials, FontBackgroundColor, FontColor, FontFamily, FontSize, GeneralHtmlSupport, Heading, Highlight, HorizontalLine, Image, ImageCaption, ImageStyle, ImageToolbar, ImageUpload, Indent, IndentBlock, Italic, Link, List, MediaEmbed, Paragraph, PasteFromOffice, RemoveFormat, SelectAll, Strikethrough, Subscript, Superscript, Table, TableCaption, TableCellProperties, TableColumnResize, TableProperties, TableToolbar, TextTransformation, Underline, NonBreakingSpace];
  static defaultConfig = { licenseKey: 'GPL', language: 'en' };
}
window.ClassicEditor = H5PEditor;
