/**
 * @license Copyright (c) 2003-2022, CKSource Holding sp. z o.o. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */

CKEDITOR.editorConfig = function( config ) {
	// Define changes to default configuration here. For example:
	// config.language = 'fr';
	// config.uiColor = '#AADC6E';
	//config.format_tags='div;h1;h2;pre;'
config.wordcount = {
            maxCharCount: 3500, // Matches your Django form limit
            showWordCount: true,
            showCharCount: true
        };
};
