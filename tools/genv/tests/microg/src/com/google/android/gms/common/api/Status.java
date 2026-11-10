package com.google.android.gms.common.api;

import android.os.Parcel;
import android.os.Parcelable;

/** Allows a synthetic probe to discard MicroG's status parcel without logging it. */
public final class Status implements Parcelable {
    @Override public int describeContents() { return 0; }
    @Override public void writeToParcel(Parcel parcel, int flags) {
        throw new UnsupportedOperationException("Read-only test stub");
    }

    public static final Creator<Status> CREATOR = new Creator<Status>() {
        @Override public Status createFromParcel(Parcel parcel) {
            int header = parcel.readInt();
            if ((header & 0xffff) != 0x4f45) throw new IllegalArgumentException("Invalid status");
            int size = (header & 0xffff0000) == 0xffff0000 ? parcel.readInt() : header >>> 16;
            parcel.setDataPosition(parcel.dataPosition() + size);
            return new Status();
        }
        @Override public Status[] newArray(int size) { return new Status[size]; }
    };
}
