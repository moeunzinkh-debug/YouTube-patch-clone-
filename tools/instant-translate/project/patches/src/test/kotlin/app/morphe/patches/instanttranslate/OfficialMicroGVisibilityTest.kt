package app.morphe.patches.instanttranslate

import java.io.ByteArrayInputStream
import javax.xml.parsers.DocumentBuilderFactory
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertNotNull

class OfficialMicroGVisibilityTest {
    private fun document(xml: String) = DocumentBuilderFactory.newInstance().apply {
        isNamespaceAware = true
    }.newDocumentBuilder().parse(ByteArrayInputStream(xml.toByteArray()))

    @Test fun addsQueryOnceAndPreservesApplication() {
        val doc = document("""<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.spaceship.screen.textcopy"><application android:name="App"/></manifest>""")
        ensureOfficialMicroGVisibility(doc)
        ensureOfficialMicroGVisibility(doc)
        val packages = doc.getElementsByTagName("package")
        assertEquals(1, packages.length)
        val entry = packages.item(0) as org.w3c.dom.Element
        assertEquals("com.google.android.gms", entry.getAttributeNS("http://schemas.android.com/apk/res/android", "name"))
        assertNotNull(doc.getElementsByTagName("application").item(0))
    }

    @Test fun preservesExistingQueriesAndRejectsOtherPackages() {
        val doc = document("""<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.spaceship.screen.textcopy"><queries><package android:name="example.other"/></queries><application/></manifest>""")
        ensureOfficialMicroGVisibility(doc)
        assertEquals(2, doc.getElementsByTagName("package").length)
        val wrong = document("""<manifest package="other.app"><application/></manifest>""")
        assertFailsWith<IllegalArgumentException> { ensureOfficialMicroGVisibility(wrong) }
    }
}
