on run argv
	
	set theURL to ""
	set theOutputFilename to ""
	set theOutputDirectory to ""
	
	if (count of argv) is greater than 0 then
		set theURL to item 1 of argv
		
		if (count of argv) is greater than 1 then
			set theOutputFilename to item 2 of argv
		end if
		
		if (count of argv) is greater than 2 then
			set theOutputDirectory to item 3 of argv
		end if
		
		tell application "Safari"
			activate
			--reopen
			
			set triedSafari to 0
			repeat
				tell application "System Events"
					if front window of process "Safari" exists then exit repeat
				end tell
				if triedSafari is greater than 20 then tell me to error "Safari is not loading" number 1
				set triedSafari to triedSafari + 1
				delay 1
			end repeat
			
			if front window exists then
				close tabs of front window
			end if
			
			delay 0.5
			open location theURL
			set bounds of front window to {0, 0, 800, 800}
			delay 8
			
			set scrollHeight to do JavaScript "document.body.scrollHeight;" in document 1
			
			tell front document
				repeat with n from 1 to (scrollHeight div 800)
					set scroll to "window.scrollTo(0," & n & "*800);"
					do JavaScript scroll
					delay 0.1
				end repeat
			end tell
			
		end tell
		
		with timeout of 60 seconds
			
			tell application "System Events"
				tell process "Safari"
					delay 0.5
					click menu item "Export as PDFÉ" of menu "File" of menu bar 1
					
					keystroke "s" using {command down, shift down, option down}
					repeat until exists sheet 1 of window 1
						delay 0.02
					end repeat
					
					if theOutputDirectory is not equal to "" then
						delay 0.5
						
						keystroke "g" using {command down, shift down}
						repeat until exists sheet 1 of sheet 1 of window 1
							delay 0.2
						end repeat
						
						delay 0.5
						
						tell sheet 1 of sheet 1 of window 1
							set value of text field 1 to theOutputDirectory
							delay 1
							set value of text field 1 to ""
							delay 0.5
							set value of text field 1 to theOutputDirectory
							delay 1
							key code 36
						end tell
						
					end if
					
					delay 0.5
					
					tell sheet 1 of window 1
						delay 0.2
						if theOutputFilename is not equal to "" then
							set value of text field 1 to theOutputFilename
						end if
						delay 0.2
						click button "Save"
					end tell
					
					-- Give Safari time to save the document
					delay 5
					
					tell application "Safari"
						quit
					end tell
				end tell
			end tell
			
		end timeout
		
	end if
end run