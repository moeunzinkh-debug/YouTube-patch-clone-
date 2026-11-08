package app.morphe.patches.genv

import java.io.ByteArrayInputStream
import javax.xml.parsers.DocumentBuilderFactory
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import org.w3c.dom.Element

class MicroGManifestTest {
    private val android = "http://schemas.android.com/apk/res/android"
    private fun parse(xml: String) = DocumentBuilderFactory.newInstance().apply { isNamespaceAware = true }
        .newDocumentBuilder().parse(ByteArrayInputStream(xml.toByteArray()))
    private fun base() = parse("""
        <manifest xmlns:android="http://schemas.android.com/apk/res/android" package="com.ainate.ai.video.generate">
          <uses-permission android:name="com.google.android.c2dm.permission.RECEIVE"/>
          <application android:name="com.google.android.gms.SomeClass">
            <receiver android:name="com.example.Receiver" android:permission="com.google.android.c2dm.permission.SEND">
              <intent-filter><action android:name="com.google.android.c2dm.intent.RECEIVE"/></intent-filter>
            </receiver>
          </application>
        </manifest>
    """.trimIndent())
    private fun Element.attr(name: String) = getAttributeNS(android, name)

    @Test fun addsExactlyOnePackageQueryAndReviewedIdentity() {
        val doc = base()
        addMorpheMicroGManifestEntries(doc)
        addMorpheMicroGManifestEntries(doc)
        assertEquals("com.ainate.ai.video.generate", doc.documentElement.getAttribute("package"))
        assertEquals("com.google.android.gms.SomeClass", (doc.getElementsByTagName("application").item(0) as Element).attr("name"))
        val packages = doc.getElementsByTagName("package")
        assertEquals(1, packages.length)
        assertEquals("app.revanced.android.gms", (packages.item(0) as Element).attr("name"))
        val metadata = doc.getElementsByTagName("meta-data")
        assertEquals(3, metadata.length)
        val values = (0 until metadata.length).map { metadata.item(it) as Element }.associate { it.attr("name") to it.attr("value") }
        assertEquals("com.ainate.ai.video.generate", values["app.revanced.android.gms.SPOOFED_PACKAGE_NAME"])
        assertEquals("be4c81d3869d726ea9f0229ab937f2e11ab1ccc7", values["app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE"])
        assertEquals("app.revanced.android.gms", values["app.revanced.MICROG_PACKAGE_NAME"])
        assertEquals("app.revanced.android.c2dm.permission.RECEIVE", (doc.getElementsByTagName("uses-permission").item(0) as Element).attr("name"))
        assertEquals("app.revanced.android.c2dm.permission.SEND", (doc.getElementsByTagName("receiver").item(0) as Element).attr("permission"))
        assertEquals("app.revanced.android.c2dm.intent.RECEIVE", (doc.getElementsByTagName("action").item(0) as Element).attr("name"))
    }

    @Test fun rejectsWrongPackageOrConflictingMetadata() {
        val wrong = base().apply { documentElement.setAttribute("package", "com.example.other") }
        assertFailsWith<IllegalArgumentException> { addMorpheMicroGManifestEntries(wrong) }
        val conflict = base()
        val app = conflict.getElementsByTagName("application").item(0) as Element
        app.appendChild(conflict.createElement("meta-data").apply {
            setAttributeNS(android, "android:name", "app.revanced.android.gms.SPOOFED_PACKAGE_SIGNATURE")
            setAttributeNS(android, "android:value", "bad")
        })
        assertFailsWith<IllegalArgumentException> { addMorpheMicroGManifestEntries(conflict) }
    }
}
