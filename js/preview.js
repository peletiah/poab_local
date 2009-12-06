function ShowPreview()
{
 var hWndPreviewWindow =
window.open("","Preview","width=400,height=250,scrollbars=yes,resizable=yes,status=0");

    hWndPreviewWindow.document.open();
    hWndPreviewWindow.document.writeln('<HTML><HEAD><TITLE>Your Preview Window</TITLE></HEAD>');
    hWndPreviewWindow.document.writeln('<BODY BGCOLOR="lightyellow">');
    hWndPreviewWindow.document.writeln('<B>Here is your text</B>');
    hWndPreviewWindow.document.writeln('<A HREF="javascript:window.close()">Close Preview</A><BR>');

hWndPreviewWindow.document.writeln(document.SampleForm.MessageText.value);
    hWndPreviewWindow.document.writeln('</BODY></HTML>');
    hWndPreviewWindow.document.close();
}
