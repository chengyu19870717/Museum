import SwiftUI
import UIKit

/// Fixes Chinese IME real-time search for SwiftUI .searchable.
///
/// SwiftUI's .searchable binding only updates when IME commits a character
/// (e.g., after tapping a candidate). During composition (underlined pinyin),
/// UITextField.text is empty and the binding never fires.
///
/// This modifier intercepts UITextField.textDidChangeNotification to get
/// the committed text + the in-progress marked text, then updates the binding
/// so the filter runs on every keystroke — giving real-time results while typing.
struct IMESearchModifier: ViewModifier {
    @Binding var searchText: String

    func body(content: Content) -> some View {
        content.onReceive(
            NotificationCenter.default
                .publisher(for: UITextField.textDidChangeNotification)
        ) { note in
            guard let tf = note.object as? UITextField,
                  tf.isFirstResponder
            else { return }

            let committed = tf.text ?? ""

            // markedTextRange is set when the user is mid-composition (underlined pinyin)
            let marked: String = {
                guard let range = tf.markedTextRange else { return "" }
                return tf.text(in: range) ?? ""
            }()

            // Build the effective query: committed chars + live composition
            let effective = committed + marked

            // Guard: avoid re-triggering the notification by suppressing no-op writes
            if searchText != effective {
                searchText = effective
            }
        }
    }
}

extension View {
    /// Apply Chinese IME real-time search fix to a view containing .searchable.
    func imeSearchFix(text: Binding<String>) -> some View {
        modifier(IMESearchModifier(searchText: text))
    }
}
