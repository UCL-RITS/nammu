'''
Copyright 2015, 2016 University College London.

This file is part of Nammu.

Nammu is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Nammu is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Nammu.  If not, see <http://www.gnu.org/licenses/>.
'''

from javax.swing.undo import CannotUndoException, CannotRedoException

from ..view.AtfAreaView import AtfAreaView
from ..view.LineNumbersArea import LineNumbersArea
from ..view.AtfEditArea import AtfEditArea
from ..view.SyntaxHighlighter import SyntaxHighlighter


class AtfAreaController(object):
    '''
    Creates the ATF area (edit/object) view and handles its actions.
    '''
    def __init__(self, mainControler):
        # Create text edition area
        self.edit_area = AtfEditArea(self)
        # Create text panel to display the line numbers
        self.line_numbers_area = LineNumbersArea()
        # Create view with a reference to its controller to handle events
        self.view = AtfAreaView(self)
        # Will also need delegating to parent presenter
        self.controller = mainControler
        # Get a reference to the view's undo_manager
        self.undo_manager = self.view.undo_manager
        # Initialise validation errors
        self.validation_errors = {}
        # Needed by syntax highlighter
        self.edit_area_styledoc = self.edit_area.getStyledDocument()
        self.line_numbers_styledoc = self.line_numbers_area.getStyledDocument()
        # Syntax highlighting
        self.syntax_highlighter = SyntaxHighlighter(self)

    def setAtfAreaText(self, text):
        '''
        Need to manually force an edit compound because the setText() method
        triggers 2 consecutive INSERT events: one to set the text to "" and
        another to set the text to the given text.
        Default behaviour of the compound edit would create a new edit for each
        INSERT event, so we have to manually group those two together.
        '''
        with self.view.edit_listener.force_compound():
            self.view.edit_area.setText(text)

    def getAtfAreaText(self):
        '''
        Short hand for getting Nammu's text area's content.
        '''
        return self.view.edit_area.getText()

    def clearAtfArea(self):
        '''
        Every time we clear the ATF text area we also need to clear the edits
        pile, repaint the line numbers and remove the styling from previous
        validation highlight.
        '''
        self.view.edit_area.setText("")
        # When opening a new file we should discard the previous edits
        self.view.undo_manager.discardAllEdits()
        # Reload line numbers text panel
        self.repaint_line_numbers(0)
        # Clear tooltips
        self.clearToolTips()
        # Clear validation errors
        self.validation_errors = {}

    def clearToolTips(self):
        '''
        We don't want tooltips from previous validations appearing after the
        file has been re-validated or another file has been opened.
        '''
        self.view.edit_area.setToolTipText(None)

    def update_line_numbers(self):
        '''
        Update line numbers area when text length changes.
        '''
        # Get how many lines are in the file
        n_lines = self.getAtfAreaText().count('\n')
        # Reload line numbers text panel
        self.repaint_line_numbers(n_lines)

    def set_validation_errors(self, validation_errors):
        '''
        Short hand for refreshing validation errors in ATF area.
        '''
        self.validation_errors = validation_errors

    def undo(self):
        '''
        CompoundEdits only get added  to the undo manager when the next
        INSERT/REMOVE event happens. Thus, if we are adding changes to
        the current compound edit and we want to undo it before the next
        INSERT/REMOVE happens, we won't be able until it's been explicitly
        ended.
        '''
        self.view.edit_listener.current_compound.end()
        try:
            self.undo_manager.undo()
        except CannotUndoException:
            # This exception indicates we've reached the end of the edits
            # vector Nothing to do
            pass
        else:
            self.syntax_highlight()
            self.update_line_numbers()

    def redo(self):
        try:
            self.undo_manager.redo()
        except CannotRedoException:
            # This exception indicates we've reached the end of the edits
            # vector - Nothing to do
            pass
        else:
            self.syntax_highlight()
            self.update_line_numbers()

    def __getattr__(self, name):
        '''
        Calls to copy, paste and cut methods are just passed to text area.
        '''
        if name in ('copy', 'paste', 'cut'):
            return getattr(self.view.edit_area, name)

    def repaint_line_numbers(self, n_lines):
        '''
        Draws line numbers in corresponding panel.
        '''
        # Create line numbers
        numbers = ""
        for line in range(n_lines + 1):
            numbers += str(line + 1) + ": \n"

        # Print in line numbers' area
        self.line_numbers_area.setText(numbers)

    def syntax_highlight(self):
        '''
        Short hand for syntax highlighting.
        '''
        self.syntax_highlighter.syntax_highlight()
